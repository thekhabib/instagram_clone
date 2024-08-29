import re

from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.core.validators import FileExtensionValidator
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken

from shared.utility import check_email_or_phone, send_email, check_user_type, username_regex
from users.models import User, VIA_EMAIL, VIA_PHONE, NEW, CODE_VERIFIED, DONE, PHOTO_DONE


class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    def __init__(self, *args, **kwargs):
        super(SignUpSerializer, self).__init__(*args, **kwargs)
        self.fields['email_phone_number'] = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'auth_type',
            'auth_status',
        )
        extra_kwargs = {
            'auth_type': {'read_only': True, 'required': False},
            'auth_status': {'read_only': True, 'required': False},
        }

    def create(self, validated_data):
        user = super(SignUpSerializer, self).create(validated_data)
        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_email(user.phone_number, code)
            # send_phone_number(user.phone_number, code)
        user.save()
        return user

    def validate(self, data):
        super(SignUpSerializer, self).validate(data)
        data = self.auth_validate(data)
        return data

    @staticmethod
    def auth_validate(data):
        user_input = str(data.get('email_phone_number')).lower()
        input_type = check_email_or_phone(user_input)
        if input_type == 'email':
            data = {
                'email': user_input,
                'auth_type': VIA_EMAIL,
            }
        elif input_type == 'phone':
            data = {
                'phone_number': user_input,
                'auth_type': VIA_PHONE,
            }
        else:
            error = {
                'success': False,
                'message': "Invalid email or phone number",
            }
            raise ValidationError(error)

        return data

    def validate_email_phone_number(self, value):
        value = value.lower()
        if value and User.objects.filter(email=value).exists():
            error = {
                'success': False,
                'message': 'This email is already in use',
            }
            raise ValidationError(error)
        elif value and User.objects.filter(phone_number=value).exists():
            error = {
                'success': False,
                'message': 'This phone number is already in use',
            }
            raise ValidationError(error)

        return value

    def to_representation(self, instance):
        data = super(SignUpSerializer, self).to_representation(instance)
        data.update(instance.token())
        return data


class ChangeUserInfoSerializer(serializers.Serializer):
    first_name = serializers.CharField(min_length=1, max_length=30, required=True, write_only=True)
    last_name = serializers.CharField(min_length=1, max_length=30, required=True, write_only=True)
    username = serializers.CharField(min_length=5, max_length=30, required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)
        if password != confirm_password:
            raise ValidationError(
                {
                    'success': False,
                    'message': 'Passwords mismatch',
                }
            )
        if password:
            validate_password(password)
        if not first_name.isalpha():
            raise ValidationError(
                {
                    'success': False,
                    'message': 'First name must contain only letters',
                }
            )
        if not last_name.isalpha():
            raise ValidationError(
                {
                    'success': False,
                    'message': 'Last name must contain only letters',
                }
            )

        return data

    def validate_username(self, username):
        if username.isdigit():
            raise ValidationError(
                {
                    'success': False,
                    'message': 'Username cannot contain only numbers',
                }
            )
        if not username[0].isalpha():
            raise ValidationError(
                {
                    'success': False,
                    'message': 'The first character of username must be a letter',
                }
            )
        if not username[-1].isalnum():
            raise ValidationError(
                {
                    'success': False,
                    'message': "The last character of username must be a letter or number"
                }
            )
        if not re.fullmatch(username_regex, username):
            raise ValidationError(
                {
                    'success': False,
                    'message': "Username can be a letter, number, and underscores(_)",
                }
            )
        return username

    def update(self, instance, validated_data):

        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.username = validated_data.get('username', instance.username)
        instance.password = validated_data.get('password', instance.password)
        if validated_data.get('password'):
            instance.set_password(validated_data.get('password'))
        if instance.auth_status == CODE_VERIFIED:
            instance.auth_status = DONE
        instance.save()

        return instance


class ChangeUserPhotoSerializer(serializers.Serializer):
    photo = serializers.ImageField(validators=[FileExtensionValidator(allowed_extensions=[
        'png', 'jpg', 'jpeg', 'heif', 'hevc'
    ])])

    def update(self, instance, validated_data):
        photo = validated_data.get('photo')
        if photo:
            instance.photo = photo
            instance.auth_status = PHOTO_DONE
            instance.save()
        return instance


class LoginSerializer(TokenObtainPairSerializer):

    def __init__(self, *args, **kwargs):
        super(LoginSerializer, self).__init__(*args, **kwargs)
        self.user = None
        self.fields['user_input'] = serializers.CharField(required=True)
        self.fields['username'] = serializers.CharField(required=False, read_only=True)

    def auth_validate(self, data):
        user_input = data.get('user_input')
        user_type = check_user_type(user_input)
        if user_type == 'username':
            username = user_input
        elif user_type == 'email':
            user = self.get_user(email__iexact=user_input)
            username = user.username
        elif user_type == 'phone':
            user = self.get_user(phone_number=user_input)
            username = user.username
        else:
            error = {
                'success': False,
                'message': "You must enter a username, email or phone number"
            }
            raise ValidationError(error)
        authentication_kwargs = {
            self.username_field: username,
            'password': data.get('password'),
        }

        current_user = self.get_user(username=username)
        if current_user.auth_status in [NEW, CODE_VERIFIED]:
            raise ValidationError(
                {
                    'success': False,
                    'message': "Registration is incomplete",
                }
            )

        user = authenticate(**authentication_kwargs)
        if user is not None:
            self.user = user
        else:
            raise ValidationError(
                {
                    'success': False,
                    'message': 'Sorry, login or password you entered is incorrect. Please check and try again'
                }
            )

    def validate(self, data):
        self.auth_validate(data)
        if self.user.auth_status not in [DONE, PHOTO_DONE]:
            raise PermissionDenied("You do not have permission to login!")
        data = self.user.token()
        data['auth_status'] = self.user.auth_status
        data['full_name'] = self.user.full_name
        return data

    def get_user(self, **kwargs):
        users = User.objects.filter(**kwargs)
        if not users.exists():
            raise ValidationError(
                {
                    'success': False,
                    'message': "No active account found",
                }
            )
        return users.first()


class LoginRefreshSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        data = super(LoginRefreshSerializer, self).validate(attrs)
        access_token_instance = AccessToken(data.get('access'))
        user_id = access_token_instance.get('user_id')
        user = get_object_or_404(User, id=user_id)
        update_last_login(None, user)
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ForgotPasswordserializer(serializers.Serializer):
    email_or_phone = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        email_or_phone = str(data.get('email_or_phone', None)).lower()
        if not email_or_phone:
            raise ValidationError(
                {
                    'success': False,
                    'message': "You must enter a valid email address or phone number"
                }
            )
        user = User.objects.filter(Q(email__iexact=email_or_phone) | Q(phone_number=email_or_phone))
        if not user.exists():
            raise NotFound(detail="User not found")
        data['user'] = user.first()

        return data


class ResetPasswordSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    password = serializers.CharField(min_length=8, write_only=True, required=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'id',
            'password',
            'confirm_password',
        )

    def validate(self, data):
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)
        if password != confirm_password:
            raise ValidationError(
                {
                    'success': False,
                    'message': "Passwords mismatch",
                }
            )
        if password:
            validate_password(password)
        return data

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance.set_password(password)
        return super(ResetPasswordSerializer, self).update(instance, validated_data)
