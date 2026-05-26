from datetime import timedelta
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods, require_POST

from accounts.models import User
from .decorators import role_required
from .forms import AttendanceNoteForm, EmployeeProfileForm, PayrollForm, SecureLoginForm
from .models import Attendance, AuditLog, EmployeeProfile, LoginAttempt, Payroll
from .utils import get_client_ip, sanitize_text


HR_ROLES = {User.ROLE_HR, User.ROLE_ADMIN}
PAYROLL_REVIEW_ROLES = {User.ROLE_FINANCE, User.ROLE_ADMIN}
MANAGER_ROLES = {User.ROLE_MANAGER, User.ROLE_HR, User.ROLE_ADMIN}


def write_audit(request, action: str, target: str, detail: str):
    AuditLog.objects.create(
        actor=request.user if request.user.is_authenticated else None,
        action=action,
        target=target,
        detail=detail,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
    )


def login_identifier(request, username: str) -> str:
    ip_address = get_client_ip(request)
    return f"{username.lower()}|{ip_address}"




def extract_safe_employee_id(raw_query: str) -> str:
    """Extract only the employee ID fragment from a search payload.

    The search box is intentionally strict. A payload such as
    EMP001' OR '1'='1' -- becomes EMP001, then the ORM performs an exact
    lookup. No raw SQL is built from the user input.
    """
    cleaned = sanitize_text(raw_query).upper()
    match = re.search(r"\bEMP-?[0-9]{3,8}\b", cleaned)
    return match.group(0) if match else ""


def build_employee_id_variants(employee_id: str) -> set[str]:
    compact = employee_id.replace("-", "")
    variants = {employee_id, compact}
    if compact.startswith("EMP") and len(compact) > 3:
        variants.add(f"EMP-{compact[3:]}")
    return variants


def filter_employee_queryset(queryset, raw_query: str):
    cleaned = sanitize_text(raw_query)
    if not cleaned:
        return queryset

    employee_id = extract_safe_employee_id(cleaned)
    if employee_id:
        return queryset.filter(employee_id__in=build_employee_id_variants(employee_id))

    # For non-ID search, use a conservative allowlist and Django ORM icontains.
    if not re.fullmatch(r"[A-Za-zÀ-ÿ0-9 .@_+\-/]{1,80}", cleaned):
        return queryset.none()

    return queryset.filter(
        Q(employee_id__icontains=cleaned)
        | Q(full_name__icontains=cleaned)
        | Q(position__icontains=cleaned)
        | Q(email__icontains=cleaned)
        | Q(department__name__icontains=cleaned)
    )

def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "core/home.html", {"form": SecureLoginForm(request)})


@csrf_protect
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = SecureLoginForm(request, data=request.POST or None)

    if request.method == "POST":
        posted_username = request.POST.get("username", "").strip().lower()
        identifier = login_identifier(request, posted_username)
        attempt, _ = LoginAttempt.objects.get_or_create(identifier=identifier)

        if attempt.is_locked():
            messages.error(request, "Akun atau alamat IP sementara dikunci karena terlalu banyak percobaan gagal.")
            return render(request, "core/login.html", {"form": form}, status=403)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            request.session.cycle_key()
            attempt.reset()
            write_audit(request, "login_success", user.username, "Pengguna berhasil masuk ke sistem.")
            messages.success(request, f"Selamat datang, {user.display_name or user.username}.")
            return redirect("dashboard")

        attempt.failed_count += 1
        attempt.last_failed_at = timezone.now()
        if attempt.failed_count >= settings.LOGIN_MAX_FAILED_ATTEMPTS:
            attempt.locked_until = timezone.now() + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
        attempt.save(update_fields=["failed_count", "last_failed_at", "locked_until"])
        AuditLog.objects.create(
            actor=None,
            action="login_failed",
            target=posted_username[:120],
            detail="Percobaan login gagal dicatat tanpa menyimpan password.",
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
        )
        messages.error(request, "Username atau password tidak valid.")

    template_name = "core/login.html" if request.path == "/login/" else "core/home.html"
    return render(request, template_name, {"form": form})


@require_POST
@login_required
def logout_view(request):
    write_audit(request, "logout", request.user.username, "Pengguna keluar dari sistem.")
    logout(request)
    messages.info(request, "Anda sudah logout.")
    return redirect("login")


@login_required
def dashboard(request):
    profile = getattr(request.user, "employee_profile", None)
    context = {
        "employee_count": EmployeeProfile.objects.count(),
        "attendance_count": Attendance.objects.filter(attendance_date=timezone.localdate()).count(),
        "payroll_count": Payroll.objects.count(),
        "recent_logs": AuditLog.objects.select_related("actor")[:8],
        "profile": profile,
    }
    return render(request, "core/dashboard.html", context)


@role_required(User.ROLE_HR, User.ROLE_ADMIN, User.ROLE_MANAGER)
def employee_list(request):
    queryset = EmployeeProfile.objects.select_related("user", "department", "manager")
    if request.user.role == User.ROLE_MANAGER and not request.user.is_superuser:
        queryset = queryset.filter(manager=request.user)
    query = request.GET.get("q", "")
    queryset = filter_employee_queryset(queryset, query)
    return render(request, "core/employee_list.html", {"employees": queryset[:50], "q": sanitize_text(query)})


@role_required(User.ROLE_HR, User.ROLE_ADMIN)
@require_http_methods(["GET", "POST"])
def employee_create(request):
    form = EmployeeProfileForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        employee = form.save()
        write_audit(request, "employee_create", employee.employee_id, "Data karyawan baru dibuat oleh HR.")
        messages.success(request, "Data karyawan berhasil ditambahkan.")
        return redirect("employee_detail", pk=employee.pk)
    return render(request, "core/employee_form.html", {"form": form, "mode": "create"})


@role_required(User.ROLE_HR, User.ROLE_ADMIN)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def employee_update(request, pk):
    employee = get_object_or_404(EmployeeProfile.objects.select_related("department"), pk=pk)
    before = {
        "full_name": employee.full_name,
        "position": employee.position,
        "base_salary": str(employee.base_salary),
        "status": employee.status,
    }
    form = EmployeeProfileForm(request.POST or None, instance=employee)
    if request.method == "POST" and form.is_valid():
        employee = form.save()
        after = {
            "full_name": employee.full_name,
            "position": employee.position,
            "base_salary": str(employee.base_salary),
            "status": employee.status,
        }
        write_audit(request, "employee_update", employee.employee_id, f"Data karyawan diperbarui. before={before}; after={after}")
        messages.success(request, "Data karyawan berhasil diperbarui.")
        return redirect("employee_detail", pk=employee.pk)
    return render(request, "core/employee_form.html", {"form": form, "employee": employee, "mode": "update"})


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(EmployeeProfile.objects.select_related("user", "department", "manager"), pk=pk)
    allowed = request.user.is_superuser or request.user.role in HR_ROLES or employee.user_id == request.user.id
    allowed = allowed or (request.user.role == User.ROLE_MANAGER and employee.manager_id == request.user.id)
    if not allowed:
        raise PermissionDenied
    return render(request, "core/employee_detail.html", {"employee": employee})


@login_required
def my_profile(request):
    profile = getattr(request.user, "employee_profile", None)
    if not profile:
        messages.warning(request, "Akun ini belum memiliki profil karyawan.")
        return redirect("dashboard")
    return redirect("employee_detail", pk=profile.pk)


@login_required
def attendance_list(request):
    queryset = Attendance.objects.select_related("employee", "employee__department")
    if request.user.role == User.ROLE_EMPLOYEE and not request.user.is_superuser:
        profile = getattr(request.user, "employee_profile", None)
        queryset = queryset.filter(employee=profile) if profile else queryset.none()
    elif request.user.role == User.ROLE_MANAGER and not request.user.is_superuser:
        queryset = queryset.filter(employee__manager=request.user)
    return render(request, "core/attendance_list.html", {"attendances": queryset[:50]})


@require_POST
@login_required
@transaction.atomic
def attendance_check_in(request):
    profile = getattr(request.user, "employee_profile", None)
    if not profile:
        raise PermissionDenied

    form = AttendanceNoteForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Catatan absensi tidak valid.")
        return redirect("attendance_list")

    today = timezone.localdate()
    attendance, created = Attendance.objects.get_or_create(
        employee=profile,
        attendance_date=today,
        defaults={"note": form.cleaned_data["note"]},
    )
    if attendance.check_in:
        messages.warning(request, "Check in hari ini sudah tercatat.")
        return redirect("attendance_list")

    now = timezone.now()
    attendance.check_in = now
    attendance.note = form.cleaned_data["note"]
    if now.astimezone(timezone.get_current_timezone()).time().hour >= 9:
        attendance.status = Attendance.STATUS_LATE
    attendance.save()
    write_audit(request, "attendance_check_in", profile.employee_id, "Check in karyawan tercatat.")
    messages.success(request, "Check in berhasil dicatat.")
    return redirect("attendance_list")


@require_POST
@login_required
@transaction.atomic
def attendance_check_out(request):
    profile = getattr(request.user, "employee_profile", None)
    if not profile:
        raise PermissionDenied

    today = timezone.localdate()
    attendance = get_object_or_404(Attendance, employee=profile, attendance_date=today)
    if not attendance.check_in:
        messages.error(request, "Check out tidak dapat dilakukan sebelum check in.")
        return redirect("attendance_list")
    if attendance.check_out:
        messages.warning(request, "Check out hari ini sudah tercatat.")
        return redirect("attendance_list")

    attendance.check_out = timezone.now()
    attendance.save(update_fields=["check_out"])
    write_audit(request, "attendance_check_out", profile.employee_id, "Check out karyawan tercatat.")
    messages.success(request, "Check out berhasil dicatat.")
    return redirect("attendance_list")


@login_required
def payroll_list(request):
    queryset = Payroll.objects.select_related("employee", "employee__department", "created_by", "approved_by")
    if request.user.role == User.ROLE_EMPLOYEE and not request.user.is_superuser:
        profile = getattr(request.user, "employee_profile", None)
        queryset = queryset.filter(employee=profile, status__in=[Payroll.STATUS_APPROVED, Payroll.STATUS_PAID]) if profile else queryset.none()
    elif request.user.role == User.ROLE_MANAGER and not request.user.is_superuser:
        queryset = queryset.filter(employee__manager=request.user)
    return render(request, "core/payroll_list.html", {"payrolls": queryset[:50]})


@role_required(User.ROLE_HR, User.ROLE_ADMIN)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def payroll_create(request):
    form = PayrollForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        payroll = form.save(commit=False)
        payroll.created_by = request.user
        payroll.bank_account_snapshot = payroll.employee.bank_account
        payroll.full_clean()
        payroll.save()
        write_audit(request, "payroll_create", str(payroll), "Draft payroll dibuat menggunakan form tervalidasi.")
        messages.success(request, "Draft payroll berhasil dibuat.")
        return redirect("payroll_detail", pk=payroll.pk)
    return render(request, "core/payroll_form.html", {"form": form, "mode": "create"})


@role_required(User.ROLE_HR, User.ROLE_ADMIN)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def payroll_update(request, pk):
    payroll = get_object_or_404(Payroll.objects.select_related("employee"), pk=pk)
    if payroll.status not in {Payroll.STATUS_DRAFT, Payroll.STATUS_SUBMITTED}:
        messages.error(request, "Payroll yang sudah diproses tidak dapat diubah tanpa membuat draft baru.")
        return redirect("payroll_detail", pk=payroll.pk)

    before = {
        "basic_salary": str(payroll.basic_salary),
        "allowance": str(payroll.allowance),
        "deduction": str(payroll.deduction),
        "status": payroll.status,
    }
    form = PayrollForm(request.POST or None, instance=payroll)
    if request.method == "POST" and form.is_valid():
        payroll = form.save(commit=False)
        if payroll.created_by_id is None:
            payroll.created_by = request.user
        payroll.bank_account_snapshot = payroll.employee.bank_account
        payroll.full_clean()
        payroll.save()
        after = {
            "basic_salary": str(payroll.basic_salary),
            "allowance": str(payroll.allowance),
            "deduction": str(payroll.deduction),
            "status": payroll.status,
        }
        write_audit(request, "payroll_update", str(payroll), f"Draft payroll diperbarui. before={before}; after={after}")
        messages.success(request, "Draft payroll berhasil diperbarui.")
        return redirect("payroll_detail", pk=payroll.pk)
    return render(request, "core/payroll_form.html", {"form": form, "payroll": payroll, "mode": "update"})


@login_required
def payroll_detail(request, pk):
    payroll = get_object_or_404(
        Payroll.objects.select_related("employee", "employee__department", "created_by", "approved_by"),
        pk=pk,
    )
    allowed = request.user.is_superuser or request.user.role in HR_ROLES or request.user.role in PAYROLL_REVIEW_ROLES
    allowed = allowed or (payroll.employee.user_id == request.user.id and payroll.status in {Payroll.STATUS_APPROVED, Payroll.STATUS_PAID})
    allowed = allowed or (request.user.role == User.ROLE_MANAGER and payroll.employee.manager_id == request.user.id)
    if not allowed:
        raise PermissionDenied
    return render(request, "core/payroll_detail.html", {"payroll": payroll})


@require_POST
@role_required(User.ROLE_FINANCE, User.ROLE_ADMIN)
@transaction.atomic
def payroll_approve(request, pk):
    payroll = get_object_or_404(Payroll.objects.select_related("employee"), pk=pk)
    if payroll.employee.status != EmployeeProfile.STATUS_ACTIVE:
        messages.error(request, "Payroll tidak dapat disetujui karena karyawan tidak aktif.")
        return redirect("payroll_detail", pk=payroll.pk)
    if payroll.bank_account_snapshot != payroll.employee.bank_account:
        messages.error(request, "Nomor rekening payroll tidak sesuai dengan data karyawan aktif.")
        return redirect("payroll_detail", pk=payroll.pk)
    if payroll.status not in {Payroll.STATUS_DRAFT, Payroll.STATUS_SUBMITTED}:
        messages.warning(request, "Payroll ini tidak berada pada status yang dapat disetujui.")
        return redirect("payroll_detail", pk=payroll.pk)

    payroll.status = Payroll.STATUS_APPROVED
    payroll.approved_by = request.user
    payroll.approved_at = timezone.now()
    payroll.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    write_audit(request, "payroll_approve", str(payroll), "Payroll disetujui oleh Finance setelah verifikasi silang.")
    messages.success(request, "Payroll berhasil disetujui.")
    return redirect("payroll_detail", pk=payroll.pk)


@role_required(User.ROLE_HR, User.ROLE_ADMIN)
def audit_log_list(request):
    logs = AuditLog.objects.select_related("actor")[:100]
    return render(request, "core/audit_log_list.html", {"logs": logs})


def permission_denied_view(request, exception=None):
    return render(request, "403.html", status=403)


def not_found_view(request, exception=None):
    return render(request, "404.html", status=404)


def csrf_failure(request, reason=""):
    return render(request, "403.html", {"reason": "CSRF token tidak valid atau tidak ditemukan."}, status=403)
