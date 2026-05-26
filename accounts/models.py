from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_EMPLOYEE = "employee"
    ROLE_MANAGER = "manager"
    ROLE_HR = "hr"
    ROLE_FINANCE = "finance"
    ROLE_ADMIN = "admin"

    ROLE_CHOICES = [
        (ROLE_EMPLOYEE, "Karyawan"),
        (ROLE_MANAGER, "Manajer Karyawan"),
        (ROLE_HR, "SDM/HR"),
        (ROLE_FINANCE, "Finance"),
        (ROLE_ADMIN, "Admin Sistem"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_EMPLOYEE)
    display_name = models.CharField(max_length=150, blank=True)

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.get_full_name() or self.username
        super().save(*args, **kwargs)

    @property
    def role_label(self) -> str:
        return dict(self.ROLE_CHOICES).get(self.role, self.role)

    def has_role(self, *roles: str) -> bool:
        return self.is_superuser or self.role in roles
