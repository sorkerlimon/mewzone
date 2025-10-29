from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTPVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin configuration"""
    
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_verified', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Role & Status', {'fields': ('role', 'is_verified')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    """OTP Verification admin configuration"""
    
    list_display = ('email', 'otp_code', 'verification_type', 'is_used', 'created_at', 'expires_at')
    list_filter = ('verification_type', 'is_used', 'created_at')
    search_fields = ('email', 'otp_code')
    readonly_fields = ('created_at', 'expires_at')
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


