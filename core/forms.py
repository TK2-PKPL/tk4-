from decimal import Decimal
import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import Attendance, EmployeeProfile, Payroll
from .utils import sanitize_text


SAFE_NAME_RE = re.compile(r"^[A-Za-zÀ-ÿ .'-]{3,120}$")
SAFE_NOTE_RE = re.compile(r"^[A-Za-z0-9À-ÿ .,()/'\-]{0,140}$")
SAFE_POSITION_RE = re.compile(r"^[A-Za-zÀ-ÿ0-9 .,&()/'\-]{2,80}$")


class SecureLoginForm(AuthenticationForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"autocomplete": "username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))

    def clean_username(self):
        return sanitize_text(self.cleaned_data["username"]).lower()


class EmployeeProfileForm(forms.ModelForm):
    class Meta:
        model = EmployeeProfile
        fields = [
            "user",
            "employee_id",
            "full_name",
            "position",
            "nik",
            "email",
            "phone",
            "address",
            "department",
            "manager",
            "bank_account",
            "leave_balance",
            "base_salary",
            "status",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_full_name(self):
        value = sanitize_text(self.cleaned_data["full_name"])
        if not SAFE_NAME_RE.match(value):
            raise ValidationError("Nama hanya boleh berisi huruf, spasi, apostrof, titik, dan tanda hubung.")
        return value

    def clean_position(self):
        value = sanitize_text(self.cleaned_data.get("position", ""))
        if not SAFE_POSITION_RE.match(value):
            raise ValidationError("Jabatan hanya boleh berisi huruf, angka, spasi, dan tanda baca aman.")
        return value

    def clean_address(self):
        value = sanitize_text(self.cleaned_data["address"])
        if len(value) < 10:
            raise ValidationError("Alamat minimal berisi 10 karakter.")
        return value

    def clean_base_salary(self):
        value = self.cleaned_data["base_salary"]
        if value < Decimal("0"):
            raise ValidationError("Gaji pokok tidak boleh bernilai negatif.")
        return value


class AttendanceNoteForm(forms.Form):
    note = forms.CharField(required=False, max_length=140)

    def clean_note(self):
        value = sanitize_text(self.cleaned_data.get("note", ""))
        if not SAFE_NOTE_RE.match(value):
            raise ValidationError("Catatan absensi mengandung karakter yang tidak diperbolehkan.")
        return value


class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = ["employee", "period", "basic_salary", "allowance", "deduction", "status"]

    def clean_period(self):
        value = sanitize_text(self.cleaned_data["period"])
        if not re.match(r"^[0-9]{4}-(0[1-9]|1[0-2])$", value):
            raise ValidationError("Periode harus menggunakan format YYYY-MM.")
        return value

    def clean(self):
        cleaned = super().clean()
        basic = cleaned.get("basic_salary") or Decimal("0")
        allowance = cleaned.get("allowance") or Decimal("0")
        deduction = cleaned.get("deduction") or Decimal("0")
        if basic < 0 or allowance < 0 or deduction < 0:
            raise ValidationError("Komponen payroll tidak boleh bernilai negatif.")
        if deduction > basic + allowance:
            raise ValidationError("Potongan tidak boleh melebihi gaji pokok dan tunjangan.")
        return cleaned
