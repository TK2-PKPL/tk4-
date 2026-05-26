from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from core.models import Attendance, AuditLog, Department, EmployeeProfile, Payroll


class Command(BaseCommand):
    help = "Mengisi data demo untuk Secure HR & Payroll Portal."

    @transaction.atomic
    def handle(self, *args, **options):
        password = "DemoPass123"
        departments = {
            "HR": Department.objects.get_or_create(code="HR", defaults={"name": "Human Resources"})[0],
            "FIN": Department.objects.get_or_create(code="FIN", defaults={"name": "Finance"})[0],
            "OPS": Department.objects.get_or_create(code="OPS", defaults={"name": "Operations"})[0],
        }

        users = {}
        data = [
            ("employee1", "employee1@example.com", "Raka Pratama", User.ROLE_EMPLOYEE),
            ("employee2", "employee2@example.com", "Nadia Lestari", User.ROLE_EMPLOYEE),
            ("manager1", "manager1@example.com", "Maya Anggraini", User.ROLE_MANAGER),
            ("hr1", "hr1@example.com", "Dimas Hartono", User.ROLE_HR),
            ("finance1", "finance1@example.com", "Sinta Maharani", User.ROLE_FINANCE),
            ("admin1", "admin1@example.com", "Admin Sistem", User.ROLE_ADMIN),
        ]

        for username, email, display_name, role in data:
            user, _ = User.objects.get_or_create(username=username, defaults={"email": email, "display_name": display_name, "role": role})
            user.email = email
            user.display_name = display_name
            user.role = role
            user.set_password(password)
            user.is_staff = role == User.ROLE_ADMIN
            user.is_superuser = role == User.ROLE_ADMIN
            user.save()
            users[username] = user

        employee_rows = [
            (users["employee1"], "EMP001", "Raka Pratama", "3173010101010001", "employee1@example.com", "081234567890", "Jl. Melati No. 10 Jakarta", departments["OPS"], users["manager1"], "123456789012", Decimal("8500000")),
            (users["employee2"], "EMP002", "Nadia Lestari", "3173010101010002", "employee2@example.com", "081234567891", "Jl. Kenanga No. 11 Jakarta", departments["OPS"], users["manager1"], "123456789013", Decimal("8000000")),
            (users["manager1"], "EMP-0100", "Maya Anggraini", "3173010101010100", "manager1@example.com", "081234567892", "Jl. Cempaka No. 20 Jakarta", departments["OPS"], None, "123456789100", Decimal("14500000")),
            (users["hr1"], "EMP-0200", "Dimas Hartono", "3173010101010200", "hr1@example.com", "081234567893", "Jl. Dahlia No. 30 Jakarta", departments["HR"], None, "123456789200", Decimal("12000000")),
            (users["finance1"], "EMP-0300", "Sinta Maharani", "3173010101010300", "finance1@example.com", "081234567894", "Jl. Anggrek No. 40 Jakarta", departments["FIN"], None, "123456789300", Decimal("12500000")),
        ]

        profiles = {}
        for row in employee_rows:
            user, employee_id, full_name, nik, email, phone, address, department, manager, bank_account, salary = row
            profile, _ = EmployeeProfile.objects.get_or_create(user=user, defaults={"employee_id": employee_id, "full_name": full_name, "nik": nik, "email": email, "phone": phone, "address": address, "department": department, "manager": manager, "bank_account": bank_account, "base_salary": salary})
            profile.employee_id = employee_id
            profile.full_name = full_name
            profile.nik = nik
            profile.email = email
            profile.phone = phone
            profile.address = address
            profile.department = department
            profile.manager = manager
            profile.bank_account = bank_account
            profile.base_salary = salary
            profile.status = EmployeeProfile.STATUS_ACTIVE
            profile.save()
            profiles[employee_id] = profile

        today = timezone.localdate()
        Attendance.objects.get_or_create(employee=profiles["EMP001"], attendance_date=today, defaults={"check_in": timezone.now(), "status": Attendance.STATUS_PRESENT, "note": "Data demo"})

        payroll, _ = Payroll.objects.get_or_create(
            employee=profiles["EMP001"],
            period="2026-04",
            defaults={
                "basic_salary": Decimal("8500000"),
                "allowance": Decimal("750000"),
                "deduction": Decimal("150000"),
                "created_by": users["hr1"],
                "status": Payroll.STATUS_SUBMITTED,
                "bank_account_snapshot": profiles["EMP001"].bank_account,
            },
        )
        payroll.basic_salary = Decimal("8500000")
        payroll.allowance = Decimal("750000")
        payroll.deduction = Decimal("150000")
        payroll.created_by = users["hr1"]
        payroll.status = Payroll.STATUS_SUBMITTED
        payroll.bank_account_snapshot = profiles["EMP001"].bank_account
        payroll.save()

        AuditLog.objects.get_or_create(
            actor=users["admin1"],
            action="seed_demo",
            target="initial_data",
            defaults={"detail": "Data demo dibuat untuk pengujian secure coding.", "ip_address": "127.0.0.1"},
        )

        self.stdout.write(self.style.SUCCESS("Data demo berhasil dibuat. Password seluruh akun demo: DemoPass123"))
