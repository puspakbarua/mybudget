from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""
    model = UserProfile
    fields = ('email_verified', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    can_delete = False


class UserAdmin(BaseUserAdmin):
    """Extended User admin with UserProfile."""
    inlines = [UserProfileInline]


class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile."""
    list_display = ('user', 'email_verified', 'created_at')
    list_filter = ('email_verified', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Info', {'fields': ('user',)}),
        ('Email Verification', {'fields': ('email_verified', 'email_verification_token', 'email_verification_token_expires_at')}),
        ('Password Reset', {'fields': ('password_reset_token', 'password_reset_token_expires_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


# Unregister and re-register User admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)

