from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from core import views

handler403 = "core.views.permission_denied_view"
handler404 = "core.views.not_found_view"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("employees/", views.employee_list, name="employee_list"),
    path("data-karyawan/", views.employee_list, name="employee_list_alias_data_karyawan"),
    path("karyawan/", views.employee_list, name="employee_list_alias_karyawan"),
    path("employees/new/", views.employee_create, name="employee_create"),
    path("employees/<int:pk>/", views.employee_detail, name="employee_detail"),
    path("employees/<int:pk>/edit/", views.employee_update, name="employee_update"),
    path("karyawan/edit/<int:pk>/", views.employee_update, name="employee_update_alias"),
    path("profile/", views.my_profile, name="my_profile"),
    path("attendance/", views.attendance_list, name="attendance_list"),
    path("attendance/check-in/", views.attendance_check_in, name="attendance_check_in"),
    path("attendance/check-out/", views.attendance_check_out, name="attendance_check_out"),
    path("payroll/", views.payroll_list, name="payroll_list"),
    path("payroll/new/", views.payroll_create, name="payroll_create"),
    path("payroll/<int:pk>/", views.payroll_detail, name="payroll_detail"),
    path("payroll/<int:pk>/update/", views.payroll_update, name="payroll_update"),
    path("payroll/update/<int:pk>/", views.payroll_update, name="payroll_update_alias"),
    path("payroll/<int:pk>/approve/", views.payroll_approve, name="payroll_approve"),
    path("audit/", views.audit_log_list, name="audit_log_list"),
    path("csrf-failed/", views.csrf_failure, name="csrf_failure"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
