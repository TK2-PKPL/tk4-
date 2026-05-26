from django.contrib import admin
from .models import Attendance, AuditLog, Department, EmployeeProfile, LoginAttempt, Payroll


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "full_name", "position", "department", "status", "base_salary")
    list_filter = ("department", "status")
    search_fields = ("employee_id", "full_name", "position", "nik", "email")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "attendance_date", "check_in", "check_out", "status")
    list_filter = ("attendance_date", "status")


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ("employee", "period", "total_salary", "status", "approved_by")
    list_filter = ("period", "status")
    search_fields = ("employee__employee_id", "employee__full_name")


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ("identifier", "failed_count", "locked_until", "last_failed_at")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "target", "ip_address")
    list_filter = ("action", "created_at")
    search_fields = ("actor__username", "action", "target", "detail")
