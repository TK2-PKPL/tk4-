from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone


class Department(models.Model):
    name = models.CharField(max_length=80, unique=True)
    code = models.CharField(
        max_length=12,
        unique=True,
        validators=[RegexValidator(r"^[A-Z0-9_]{2,12}$", "Kode hanya boleh berisi huruf kapital, angka, dan underscore.")],
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class EmployeeProfile(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_INACTIVE = "inactive"
    STATUS_RESIGNED = "resigned"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Aktif"),
        (STATUS_INACTIVE, "Nonaktif"),
        (STATUS_RESIGNED, "Resign"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employee_profile")
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(r"^EMP-?[0-9]{3,8}$", "Format ID karyawan harus seperti EMP001 atau EMP-0001.")],
    )
    full_name = models.CharField(max_length=120)
    position = models.CharField(
        max_length=80,
        default="Staff",
        validators=[RegexValidator(r"^[A-Za-zÀ-ÿ0-9 .,'/&()\-]{2,80}$", "Jabatan mengandung karakter tidak valid.")],
    )
    nik = models.CharField(
        max_length=16,
        unique=True,
        validators=[RegexValidator(r"^[0-9]{16}$", "NIK harus terdiri dari 16 digit.")],
    )
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(r"^[0-9+() -]{8,20}$", "Nomor telepon mengandung karakter tidak valid.")],
    )
    address = models.TextField(max_length=250)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="employees")
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_employees",
    )
    bank_account = models.CharField(
        max_length=20,
        validators=[RegexValidator(r"^[0-9]{8,20}$", "Nomor rekening hanya boleh berisi angka.")],
    )
    leave_balance = models.PositiveIntegerField(default=12)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee_id"]

    def __str__(self) -> str:
        return f"{self.employee_id} - {self.full_name}"


class Attendance(models.Model):
    STATUS_PRESENT = "present"
    STATUS_LATE = "late"
    STATUS_CHOICES = [
        (STATUS_PRESENT, "Hadir"),
        (STATUS_LATE, "Terlambat"),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name="attendances")
    attendance_date = models.DateField(default=timezone.localdate)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PRESENT)
    note = models.CharField(max_length=140, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-attendance_date", "employee__employee_id"]
        unique_together = ("employee", "attendance_date")

    def __str__(self) -> str:
        return f"{self.employee.employee_id} {self.attendance_date}"


class Payroll(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_APPROVED = "approved"
    STATUS_PAID = "paid"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED, "Diajukan"),
        (STATUS_APPROVED, "Disetujui"),
        (STATUS_PAID, "Dibayar"),
        (STATUS_REJECTED, "Ditolak"),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.PROTECT, related_name="payrolls")
    period = models.CharField(
        max_length=7,
        validators=[RegexValidator(r"^[0-9]{4}-(0[1-9]|1[0-2])$", "Periode harus menggunakan format YYYY-MM.")],
    )
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(Decimal("0"))])
    deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(Decimal("0"))])
    total_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bank_account_snapshot = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_payrolls")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_payrolls")
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-period", "employee__employee_id"]
        unique_together = ("employee", "period")

    def calculate_total(self) -> Decimal:
        return self.basic_salary + self.allowance - self.deduction

    def clean(self):
        super().clean()
        if self.deduction > self.basic_salary + self.allowance:
            from django.core.exceptions import ValidationError

            raise ValidationError("Potongan tidak boleh melebihi gaji pokok dan tunjangan.")

    def save(self, *args, **kwargs):
        self.total_salary = self.calculate_total()
        if self.employee_id and not self.bank_account_snapshot:
            self.bank_account_snapshot = self.employee.bank_account
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.employee.employee_id} {self.period}"


class LoginAttempt(models.Model):
    identifier = models.CharField(max_length=150, unique=True)
    failed_count = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_failed_at = models.DateTimeField(null=True, blank=True)

    def is_locked(self) -> bool:
        return bool(self.locked_until and self.locked_until > timezone.now())

    def reset(self):
        self.failed_count = 0
        self.locked_until = None
        self.last_failed_at = None
        self.save(update_fields=["failed_count", "locked_until", "last_failed_at"])


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    action = models.CharField(max_length=120)
    target = models.CharField(max_length=120, blank=True)
    detail = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.created_at} {self.action}"
