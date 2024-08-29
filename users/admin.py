from django.contrib import admin
from users.models import User, UserConfirmation


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'phone_number')


# admin.site.register(UserConfirmation)
@admin.register(UserConfirmation)
class UserConfirmationAdmin(admin.ModelAdmin):
    list_display = ('user', 'verify_type', 'expiration_time', 'is_confirmed')
