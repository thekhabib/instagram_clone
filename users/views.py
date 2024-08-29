from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from shared.utility import send_email, check_email_or_phone
from users.models import User, NEW, CODE_VERIFIED, VIA_EMAIL, VIA_PHONE
from users.serializers import SignUpSerializer, ChangeUserInfoSerializer, ChangeUserPhotoSerializer, \
    LoginSerializer, LoginRefreshSerializer, LogoutSerializer, ForgotPasswordserializer, \
    ResetPasswordSerializer


class SignUpView(CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny, ]
    serializer_class = SignUpSerializer


class VerifyAPIView(APIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        user = self.request.user
        code = request.data.get('code')
        self.check_verify(user, code)
        data = {
            'status': True,
            'auth_status': user.auth_status,
            'access_token': user.token()['access'],
            'refresh_token': user.token()['refresh_token'],
        }
        return Response(data)

    @staticmethod
    def check_verify(user, code):
        verifies = user.verify_codes.filter(expiration_time__gte=datetime.now(), code=code, is_confirmed=False)
        if code is None:
            error = {
                'success': False,
                'message': "Enter the code sent to your email"
            }
            raise ValidationError(error)
        elif not verifies.exists():
            error = {
                'status': False,
                'message': 'The verification code is incorrect or expired'
            }
            raise ValidationError(error)
        verifies.update(is_confirmed=True)
        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFIED
            user.save()
        return True


class GetNewVerificationView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self):
        user = self.request.user
        self.check_verification(user)
        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_email(user.phone_number, code)
        else:
            error = {
                'status': False,
                'message': "Invalid email or phone number"
            }
            raise ValidationError(error)
        return Response(
            data={
                'status': True,
                'message': "The verification code has been re-sent"
            }
        )

    @staticmethod
    def check_verification(user):
        verifies = user.verify_codes.filter(expiration_time__gte=datetime.now(), is_confirmed=False)
        if verifies.exists():
            error = {
                'status': False,
                'message': "Verification code has been sent to you. Please wait a while to send again"
            }
            raise ValidationError(error)
        return True


class ChangeUserInfoView(UpdateAPIView):
    permission_classes = [IsAuthenticated, ]
    serializer_class = ChangeUserInfoSerializer
    http_method_names = ['put']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        super(ChangeUserInfoView, self).update(request, *args, **kwargs)
        data = {
            'status': True,
            'message': "User information updated successfully",
            'auth_status': self.request.user.auth_status,
        }
        return Response(data, status=status.HTTP_200_OK)


class ChangeUserPhotoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request):
        serializer = ChangeUserPhotoSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            serializer.update(user, serializer.validated_data)
            return Response(
                {
                    'message': "User photo updated successfully",
                }, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class LoginRefreshView(TokenRefreshView):
    serializer_class = LoginRefreshSerializer


class LogOutView(APIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh_token = self.request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            data = {
                'success': True,
                'message': "You are logged out"
            }
            return Response(data, status=205)
        except TokenError:
            return Response(status=400)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny, ]
    serializer_class = ForgotPasswordserializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email_or_phone = serializer.validated_data.get('email_or_phone')
        user = serializer.validated_data.get('user')
        self.check_verification(user)
        if check_email_or_phone(email_or_phone) == 'phone':
            code = user.create_verify_code(VIA_PHONE)
            send_email(user.phone_number, code)
        elif check_email_or_phone(email_or_phone) == 'email':
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        return Response(
            {
                'success': True,
                'message': "Verification code has been sent",
                'auth_status': user.auth_status,
                'access': user.token()['access'],
                'refresh': user.token()['refresh_token'],
            }, status=status.HTTP_200_OK
        )

    @staticmethod
    def check_verification(user):
        verifies = user.verify_codes.filter(expiration_time__gte=datetime.now(), is_confirmed=False)
        if verifies.exists():
            error = {
                'status': False,
                'message': "Verification code has been sent to you. Please wait a while to send again"
            }
            raise ValidationError(error)
        return True


class ResetPasswordView(UpdateAPIView):
    permission_classes = [IsAuthenticated, ]
    serializer_class = ResetPasswordSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        response = super(ResetPasswordView, self).update(request, *args, **kwargs)
        try:
            user = User.objects.get(id=response.data.get('id'))
        except ObjectDoesNotExist:
            raise NotFound(detail="User not found")
        return Response(
            {
                'success': True,
                'message': "Your password has been successfully changed",
                'access': user.token()['access'],
                'refresh': user.token()['refresh_token'],
            }
        )
