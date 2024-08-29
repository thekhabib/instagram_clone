from django.urls import path

from users.views import SignUpView, VerifyAPIView, GetNewVerificationView, \
    ChangeUserInfoView, ChangeUserPhotoView, LoginView, LoginRefreshView, \
    LogOutView, ForgotPasswordView, ResetPasswordView


urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('login/refresh/', LoginRefreshView.as_view(), name='login_refresh'),
    path('logout/', LogOutView.as_view(), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('verify/', VerifyAPIView.as_view(), name='verify'),
    path('new-verify/', GetNewVerificationView.as_view(), name='new_verify'),
    path('change-user/', ChangeUserInfoView.as_view(), name='change_user_info'),
    path('change-user-photo/', ChangeUserPhotoView.as_view(), name='change_user_photo'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
]
