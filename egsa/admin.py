from django.contrib import admin
from .models import UtilityReading, UserProfile, UtilityReport


@admin.register(UtilityReading)
class UtilityReadingAdmin(admin.ModelAdmin):
    list_display = ['utility_type', 'user', 'reading_value', 'unit', 'cost', 'reading_date', 'location']
    list_filter = ['utility_type', 'reading_date', 'location']
    search_fields = ['user__username', 'utility_type', 'location']
    ordering = ['-reading_date']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'phone', 'notification_preferences', 'created_at']
    list_filter = ['department', 'notification_preferences', 'created_at']
    search_fields = ['user__username', 'user__email', 'department']


@admin.register(UtilityReport)
class UtilityReportAdmin(admin.ModelAdmin):
    list_display = ['report_name', 'user', 'report_type', 'date_generated']
    list_filter = ['report_type', 'date_generated']
    search_fields = ['user__username', 'report_name']
    ordering = ['-date_generated']
    readonly_fields = ['id', 'date_generated']
