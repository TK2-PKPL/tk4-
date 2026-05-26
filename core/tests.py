from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import PBKDF2PasswordHasher, identify_hasher
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core.forms import EmployeeProfileForm, PayrollForm
from core.models import Department, EmployeeProfile, LoginAttempt, Payroll

User = get_user_model()


class FastPBKDF2PasswordHasher(PBKDF2PasswordHasher):
    iterations = 1


@override_settings(PASSWORD_HASHERS=["core.tests.FastPBKDF2PasswordHasher"])
class SecureCodingTestCase(TestCase):
    """Unit tests mapped to General TC and S10 HR & Payroll TC."""

    def setUp(self):
        self.department = Department.objects.create(code="OPS", name="Operations")
        self.employee_user = User.objects.create_user(username="employee1", password="DemoPass123", role=User.ROLE_EMPLOYEE, display_name="Raka")
        self.employee2_user = User.objects.create_user(username="employee2", password="DemoPass123", role=User.ROLE_EMPLOYEE, display_name="Nadia")
        self.manager_user = User.objects.create_user(username="manager1", password="DemoPass123", role=User.ROLE_MANAGER, display_name="Maya")
        self.hr_user = User.objects.create_user(username="hr1", password="DemoPass123", role=User.ROLE_HR, display_name="HR")
        self.finance_user = User.objects.create_user(username="finance1", password="DemoPass123", role=User.ROLE_FINANCE, display_name="Finance")
        self.profile = EmployeeProfile.objects.create(
            user=self.employee_user, employee_id="EMP001", full_name="Raka Pratama", position="Staff Operasional",
            nik="3173010101010001", email="employee1@example.com", phone="081234567890", address="Jl. Melati No. 10 Jakarta",
            department=self.department, manager=self.manager_user, bank_account="123456789012", base_salary=Decimal("8500000"),
        )
        self.other_profile = EmployeeProfile.objects.create(
            user=self.employee2_user, employee_id="EMP002", full_name="Nadia Lestari", position="Staff Administrasi",
            nik="3173010101010002", email="employee2@example.com", phone="081234567891", address="Jl. Mawar No. 11 Jakarta",
            department=self.department, bank_account="123456789013", base_salary=Decimal("8000000"),
        )
        self.payroll = Payroll.objects.create(
            employee=self.profile, period="2026-04", basic_salary=Decimal("8500000"), allowance=Decimal("750000"), deduction=Decimal("150000"),
            bank_account_snapshot=self.profile.bank_account, status=Payroll.STATUS_DRAFT, created_by=self.hr_user,
        )

    def _employee_payload(self, **overrides):
        payload = {
            "user": self.employee_user.id, "employee_id": "EMP001", "full_name": "Raka Pratama", "position": "Staff Operasional",
            "nik": "3173010101010001", "email": "employee1@example.com", "phone": "081234567890", "address": "Jl. Melati No. 10 Jakarta",
            "department": self.department.id, "manager": self.manager_user.id, "bank_account": "123456789012", "leave_balance": 12,
            "base_salary": "8500000", "status": EmployeeProfile.STATUS_ACTIVE,
        }
        payload.update(overrides)
        return payload

    def _payroll_payload(self, **overrides):
        payload = {"employee": self.profile.id, "period": "2026-04", "basic_salary": "8500000", "allowance": "750000", "deduction": "150000", "status": Payroll.STATUS_DRAFT}
        payload.update(overrides)
        return payload

    def assertHasCsrfToken(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_tc_sqli_01_login_bypass_payload_fails(self):
        client = Client()
        response = client.post(reverse("login"), {"username": "' OR '1'='1' --", "password": "bebas"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", client.session)
        self.assertNotIn(reverse("dashboard"), response.get("Location", ""))

    def test_tc_sqli_02_union_based_search_does_not_extract_user_table(self):
        client = Client(); client.force_login(self.hr_user)
        response = client.get(reverse("employee_list"), {"q": "' UNION SELECT username, password, null FROM users --"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "pbkdf2_sha256")
        self.assertNotContains(response, "DemoPass123")
        self.assertNotContains(response, "Traceback")
        self.assertNotContains(response, "OperationalError")

    def test_tc_sqli_03_whitebox_uses_orm_not_raw_sql_concatenation(self):
        project_root = Path(settings.BASE_DIR)
        app_files = [p for p in list((project_root / "core").glob("*.py")) + list((project_root / "accounts").glob("*.py")) if p.name != "tests.py"]
        source = "\n".join(path.read_text(encoding="utf-8") for path in app_files)
        forbidden_fragments = ["objects.raw(", "connection.cursor(", "cursor.execute(", "\"SELECT \" +", "'SELECT '+", ".format(request.", "% request."]
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, source)

    def test_tc_sqli_04j_hr_employee_id_payload_only_returns_emp001(self):
        client = Client(); client.force_login(self.hr_user)
        response = client.get(reverse("employee_list"), {"q": "EMP001' OR '1'='1' --"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EMP001")
        self.assertContains(response, "Raka Pratama")
        self.assertNotContains(response, "EMP002")
        self.assertNotContains(response, "Nadia Lestari")

    def test_tc_ci_01_script_tag_input_is_rejected_and_not_rendered_raw(self):
        form = EmployeeProfileForm(data=self._employee_payload(full_name="<script>alert('XSS')</script>"), instance=self.profile)
        self.assertFalse(form.is_valid())
        client = Client(); client.force_login(self.hr_user)
        response = client.post(reverse("employee_update", args=[self.profile.pk]), self._employee_payload(full_name="<script>alert('XSS')</script>"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<script>alert('XSS')</script>", html=False)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.full_name, "Raka Pratama")

    def test_tc_ci_02_html_injection_is_stripped_not_rendered_as_html(self):
        payload = "<h1>Hacked</h1><img src=x onerror=alert(1)>"
        form = EmployeeProfileForm(data=self._employee_payload(position=payload), instance=self.profile)
        self.assertTrue(form.is_valid())
        self.assertNotIn("<", form.cleaned_data["position"])
        self.assertNotIn(">", form.cleaned_data["position"])
        self.assertNotIn("onerror", form.cleaned_data["position"].lower())
        client = Client(); client.force_login(self.hr_user)
        response = client.post(reverse("employee_update", args=[self.profile.pk]), self._employee_payload(position=payload))
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertNotIn("<", self.profile.position)
        self.assertNotIn(">", self.profile.position)
        detail = client.get(reverse("employee_detail", args=[self.profile.pk]))
        self.assertNotContains(detail, "<h1>Hacked</h1>", html=False)
        self.assertNotContains(detail, "onerror=alert(1)", html=False)

    def test_tc_ci_03_template_payload_is_not_evaluated(self):
        form = EmployeeProfileForm(data=self._employee_payload(full_name="{{7*7}}"), instance=self.profile)
        self.assertFalse(form.is_valid())
        client = Client(); client.force_login(self.hr_user)
        response = client.get(reverse("employee_list"), {"q": "{{7*7}}"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "49")
        self.assertNotContains(response, settings.SECRET_KEY)

    def test_tc_ci_04j_iframe_payload_in_hr_field_is_rejected(self):
        payload = '<iframe src="javascript:alert(\'hr hacked\')"></iframe>'
        form = EmployeeProfileForm(data=self._employee_payload(position=payload), instance=self.profile)
        self.assertFalse(form.is_valid())
        client = Client(); client.force_login(self.hr_user)
        response = client.post(reverse("employee_update", args=[self.profile.pk]), self._employee_payload(position=payload))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<iframe", html=False)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.position, "Staff Operasional")

    def test_tc_ba_01_password_is_hashed_with_pbkdf2_not_plaintext(self):
        stored_password = User.objects.get(username="employee1").password
        self.assertNotEqual(stored_password, "DemoPass123")
        self.assertTrue(stored_password.startswith("pbkdf2_sha256$"))
        self.assertEqual(identify_hasher(stored_password).algorithm, "pbkdf2_sha256")

    def test_tc_ba_02_login_is_locked_after_five_failed_attempts(self):
        client = Client(); url = reverse("login")
        for index in range(5):
            response = client.post(url, {"username": "employee1", "password": f"WrongPass{index + 1}"})
            self.assertEqual(response.status_code, 200)
        response = client.post(url, {"username": "employee1", "password": "WrongPass6"})
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "dikunci", status_code=403)
        attempt = LoginAttempt.objects.get(identifier__startswith="employee1|")
        self.assertEqual(attempt.failed_count, 5)
        self.assertTrue(attempt.is_locked())

    def test_tc_ba_03_old_session_cookie_cannot_access_dashboard_after_logout(self):
        client = Client(); self.assertTrue(client.login(username="employee1", password="DemoPass123"))
        old_sessionid = client.cookies[settings.SESSION_COOKIE_NAME].value
        self.assertEqual(client.get(reverse("dashboard")).status_code, 200)
        self.assertEqual(client.post(reverse("logout")).status_code, 302)
        attacker = Client(); attacker.cookies[settings.SESSION_COOKIE_NAME] = old_sessionid
        response = attacker.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(settings.LOGIN_URL, response["Location"])

    def test_tc_ba_04_protected_hr_pages_redirect_without_login(self):
        client = Client()
        for url in [reverse("payroll_list"), reverse("employee_list_alias_data_karyawan")]:
            response = client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(settings.LOGIN_URL, response["Location"])

    def test_tc_ba_05_login_error_is_generic_for_unknown_and_known_user(self):
        unknown_response = Client().post(reverse("login"), {"username": "tidakada", "password": "Whatever123"})
        known_response = Client().post(reverse("login"), {"username": "employee1", "password": "WrongPass1"})
        generic_message = "Username atau password tidak valid."
        self.assertContains(unknown_response, generic_message)
        self.assertContains(known_response, generic_message)
        for response in [unknown_response, known_response]:
            self.assertNotContains(response, "Username tidak ditemukan")
            self.assertNotContains(response, "Password salah")

    def test_tc_csrf_01_all_write_forms_render_csrf_token(self):
        employee_client = Client(); employee_client.force_login(self.employee_user)
        self.assertHasCsrfToken(employee_client.get(reverse("attendance_list")))
        self.assertHasCsrfToken(employee_client.get(reverse("dashboard")))
        hr_client = Client(); hr_client.force_login(self.hr_user)
        self.assertHasCsrfToken(hr_client.get(reverse("employee_create")))
        self.assertHasCsrfToken(hr_client.get(reverse("employee_update", args=[self.profile.pk])))
        self.assertHasCsrfToken(hr_client.get(reverse("payroll_create")))
        self.assertHasCsrfToken(hr_client.get(reverse("payroll_update", args=[self.payroll.pk])))
        finance_client = Client(); finance_client.force_login(self.finance_user)
        self.assertHasCsrfToken(finance_client.get(reverse("payroll_detail", args=[self.payroll.pk])))

    def test_tc_csrf_02_invalid_token_is_rejected_and_employee_data_unchanged(self):
        client = Client(enforce_csrf_checks=True); client.force_login(self.hr_user)
        response = client.post(reverse("employee_update", args=[self.profile.pk]), self._employee_payload(csrfmiddlewaretoken="invalid_token_12345", position="Direktur Operasional", base_salary="9900000"))
        self.assertEqual(response.status_code, 403)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.position, "Staff Operasional")
        self.assertEqual(self.profile.base_salary, Decimal("8500000.00"))

    def test_tc_csrf_03_cross_origin_post_without_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True); client.force_login(self.hr_user)
        response = client.post(reverse("payroll_update", args=[self.payroll.pk]), self._payroll_payload(basic_salary="9999999"), HTTP_ORIGIN="http://evil.example")
        self.assertEqual(response.status_code, 403)
        self.payroll.refresh_from_db()
        self.assertEqual(self.payroll.basic_salary, Decimal("8500000.00"))

    def test_tc_csrf_04j_hr_salary_or_position_update_without_valid_csrf_is_rejected(self):
        client = Client(enforce_csrf_checks=True); client.force_login(self.hr_user)
        employee_response = client.post(reverse("employee_update_alias", args=[self.profile.pk]), self._employee_payload(position="Chief Payroll Officer", base_salary="15000000"))
        payroll_response = client.post(reverse("payroll_update_alias", args=[self.payroll.pk]), self._payroll_payload(basic_salary="15000000"))
        self.assertEqual(employee_response.status_code, 403)
        self.assertEqual(payroll_response.status_code, 403)
        self.profile.refresh_from_db(); self.payroll.refresh_from_db()
        self.assertEqual(self.profile.position, "Staff Operasional")
        self.assertEqual(self.profile.base_salary, Decimal("8500000.00"))
        self.assertEqual(self.payroll.basic_salary, Decimal("8500000.00"))

    def test_payroll_formula_rejects_negative_or_excessive_deduction(self):
        form = PayrollForm(data={"employee": self.profile.id, "period": "2026-05", "basic_salary": "8500000", "allowance": "500000", "deduction": "100000", "status": Payroll.STATUS_SUBMITTED})
        self.assertTrue(form.is_valid())
        payroll = form.save(commit=False); payroll.created_by = self.hr_user; payroll.bank_account_snapshot = self.profile.bank_account; payroll.save()
        self.assertEqual(payroll.total_salary, Decimal("8900000"))
        invalid = PayrollForm(data={"employee": self.profile.id, "period": "2026-06", "basic_salary": "8500000", "allowance": "0", "deduction": "9000000", "status": Payroll.STATUS_SUBMITTED})
        self.assertFalse(invalid.is_valid())

    def test_least_privilege_employee_only_sees_approved_or_paid_own_payslips(self):
        draft = Payroll.objects.create(employee=self.profile, period="2026-07", basic_salary=Decimal("8500000"), allowance=0, deduction=0, bank_account_snapshot=self.profile.bank_account, status=Payroll.STATUS_DRAFT, created_by=self.hr_user)
        approved = Payroll.objects.create(employee=self.profile, period="2026-08", basic_salary=Decimal("8500000"), allowance=0, deduction=0, bank_account_snapshot=self.profile.bank_account, status=Payroll.STATUS_APPROVED, created_by=self.hr_user, approved_by=self.finance_user)
        other_approved = Payroll.objects.create(employee=self.other_profile, period="2026-09", basic_salary=Decimal("8000000"), allowance=0, deduction=0, bank_account_snapshot=self.other_profile.bank_account, status=Payroll.STATUS_APPROVED, created_by=self.hr_user, approved_by=self.finance_user)
        client = Client(); client.force_login(self.employee_user)
        response = client.get(reverse("payroll_list"))
        self.assertContains(response, approved.period)
        self.assertNotContains(response, draft.period)
        self.assertNotContains(response, other_approved.period)

    def test_least_privilege_manager_only_sees_direct_reports(self):
        client = Client(); client.force_login(self.manager_user)
        response = client.get(reverse("employee_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EMP001")
        self.assertNotContains(response, "EMP002")
