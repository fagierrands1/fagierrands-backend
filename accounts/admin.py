from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.http import FileResponse
from .models import User, Profile, AssistantVerification, EmailVerification, OTPVerification


def export_users_to_excel(modeladmin, request, queryset):
    from admin_dashboard.utils.excel_export import ExcelExporter
    
    exporter = ExcelExporter('users.xlsx')
    fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 
              'user_type', 'is_verified', 'email_verified', 'is_online', 'created_at']
    headers = ['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Phone', 
               'User Type', 'Verified', 'Email Verified', 'Online', 'Created']
    exporter.add_queryset(queryset, fields, headers)
    filepath = exporter.save()
    
    response = FileResponse(
        open(filepath, 'rb'),
        as_attachment=True,
        filename='users.xlsx',
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    return response

export_users_to_excel.short_description = "Export selected users to Excel"


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        (_('Status'), {'fields': ('user_type', 'is_verified', 'email_verified')}),
        (_('Account Management'), {'fields': ('account_manager',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'account_manager', 'is_verified', 'is_staff')
    list_filter = ('user_type', 'is_verified', 'is_staff', 'is_superuser', 'is_active', 'account_manager')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')
    actions = [export_users_to_excel]

class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_used', 'is_expired')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'user__username', 'token')
    readonly_fields = ('token', 'created_at', 'expires_at')
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'

class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code', 'created_at', 'expires_at', 'is_used', 'attempts', 'is_expired')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'user__username', 'otp_code')
    readonly_fields = ('otp_code', 'created_at', 'expires_at')
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'

def export_profiles_to_excel(modeladmin, request, queryset):
    from admin_dashboard.utils.excel_export import ExcelExporter
    
    exporter = ExcelExporter('profiles.xlsx')
    fields = ['user__id', 'user__username', 'user__email', 'address', 'wallet_points', 'wallet_balance']
    headers = ['User ID', 'Username', 'Email', 'Address', 'Wallet Points', 'Wallet Balance']
    exporter.add_queryset(queryset, fields, headers)
    filepath = exporter.save()
    
    response = FileResponse(
        open(filepath, 'rb'),
        as_attachment=True,
        filename='profiles.xlsx',
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    return response

export_profiles_to_excel.short_description = "Export selected profiles to Excel"


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'wallet_points', 'wallet_balance')
    search_fields = ('user__username', 'user__email', 'address')
    actions = [export_profiles_to_excel]


admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(AssistantVerification)
admin.site.register(EmailVerification, EmailVerificationAdmin)
admin.site.register(OTPVerification, OTPVerificationAdmin)