# Tugas 4 Kelompok 52 - Unit Testing, Pentesting, dan User Acceptance Testing

## 1. Identitas Proyek

| Komponen | Keterangan |
|---|---|
| Mata kuliah | Pengantar Keamanan Perangkat Lunak - C |
| Tugas | Tugas 4 Kelompok |
| Kelompok | 52 |
| Nama kelompok | Eigen dan Orang Baik |
| Target aplikasi | Secure HR & Payroll Portal |
| Framework | Django 6 |
| Database | SQLite |
| Bahasa | Python |
| Fokus pengujian | Unit Testing, Pentesting, User Acceptance Testing, Operational Acceptance Testing |

## 2. Link Video Demo

Link video YouTube Unlisted: https://youtu.be/QJkPfljkLCE?si=p4_14dYbqTLFwwYc

## 3. Ringkasan Aplikasi yang Diuji

Aplikasi yang diuji adalah **Secure HR & Payroll Portal**, yaitu aplikasi web sederhana berbasis Django dan SQLite untuk skenario **Sistem HR & Payroll Perusahaan**. Aplikasi ini melanjutkan skenario Tugas 1 dan implementasi secure coding pada Tugas 3.

Fitur utama aplikasi meliputi:

1. Manajemen data karyawan oleh HR dan admin.
2. Tampilan data bawahan langsung oleh manajer.
3. Check in dan check out absensi oleh karyawan.
4. Pembuatan dan pembaruan draft payroll oleh HR.
5. Approval payroll oleh Finance.
6. Tampilan slip gaji yang sudah disetujui atau dibayar oleh karyawan.
7. Audit log untuk mencatat aksi penting.

Role pengguna yang digunakan:

| Role | Hak akses utama |
|---|---|
| Karyawan | Melihat profil sendiri, absensi, dan slip gaji approved atau paid |
| Manajer Karyawan | Melihat data bawahan langsung dan absensi tim |
| SDM/HR | Mengelola master data karyawan dan draft payroll |
| Finance | Menyetujui payroll setelah validasi data karyawan dan rekening |
| Admin Sistem | Akses administratif untuk pengujian dan pengelolaan sistem |

## 4. Cara Menjalankan Aplikasi

### 4.1 Persiapan Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Untuk Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4.2 Migrasi dan Data Demo

```bash
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

Akun demo yang tersedia:

| Username | Password | Role |
|---|---|---|
| employee1 | DemoPass123 | Karyawan |
| employee2 | DemoPass123 | Karyawan |
| manager1 | DemoPass123 | Manajer Karyawan |
| hr1 | DemoPass123 | SDM/HR |
| finance1 | DemoPass123 | Finance |
| admin1 | DemoPass123 | Admin Sistem |

## 5. Laporan Unit Testing

### 5.1 Tujuan Unit Testing

Unit testing dilakukan untuk memastikan fungsi keamanan yang sudah diterapkan pada Tugas 3 berjalan sesuai kebutuhan. Fokus unit testing mencakup empat area utama:

1. Code Injection Prevention.
2. Broken Authentication Mitigation.
3. CSRF Protection.
4. SQL Injection Prevention.

Selain itu, beberapa test tambahan dibuat untuk memeriksa kontrol bisnis yang berhubungan dengan keamanan, seperti validasi payroll dan prinsip least privilege.

### 5.2 Metodologi Unit Testing

Metodologi yang digunakan:

1. Menggunakan `django.test.TestCase` agar setiap test berjalan pada database test yang terisolasi.
2. Menggunakan `Client()` untuk mensimulasikan request HTTP.
3. Menggunakan `force_login()` untuk menguji hak akses berdasarkan role.
4. Menggunakan `enforce_csrf_checks=True` untuk memastikan perlindungan CSRF benar-benar diuji.
5. Menggunakan white-box inspection untuk memastikan tidak ada raw SQL berbahaya pada source code utama.
6. Menggunakan test payload berbahaya yang mewakili XSS, template injection, SQL injection, brute force, dan CSRF.

Command menjalankan unit test:

```bash
python manage.py test core -v 2
```

Lokasi file unit test:

```text
core/tests.py
```

Lokasi log hasil test:

```text
docs/test-logs/tugas4_unit_test_result.txt
```

### 5.3 Ringkasan Hasil Unit Testing

Hasil eksekusi terakhir:

```text
Found 20 test(s).
Ran 20 tests in 0.745s
OK
System check identified no issues (0 silenced).
```

Kesimpulan: seluruh unit test lulus. Artinya, fungsi keamanan utama bekerja sesuai ekspektasi pada lingkungan pengujian lokal.

### 5.4 Mapping Unit Test

| Area | TC-ID | Nama pengujian | Unit test | Hasil |
|---|---:|---|---|---|
| SQL Injection | TC-SQLi-01 | Login bypass via SQL injection | `test_tc_sqli_01_login_bypass_payload_fails` | Lulus |
| SQL Injection | TC-SQLi-02 | UNION extraction via search | `test_tc_sqli_02_union_based_search_does_not_extract_user_table` | Lulus |
| SQL Injection | TC-SQLi-03 | White-box ORM verification | `test_tc_sqli_03_whitebox_uses_orm_not_raw_sql_concatenation` | Lulus |
| SQL Injection | TC-SQLi-04 | Payload employee ID hanya mengembalikan data target | `test_tc_sqli_04j_hr_employee_id_payload_only_returns_emp001` | Lulus |
| Code Injection | TC-CI-01 | Script tag injection ditolak | `test_tc_ci_01_script_tag_input_is_rejected_and_not_rendered_raw` | Lulus |
| Code Injection | TC-CI-02 | HTML injection disanitasi | `test_tc_ci_02_html_injection_is_stripped_not_rendered_as_html` | Lulus |
| Code Injection | TC-CI-03 | Template payload tidak dievaluasi | `test_tc_ci_03_template_payload_is_not_evaluated` | Lulus |
| Code Injection | TC-CI-04 | Iframe payload pada field HR ditolak | `test_tc_ci_04j_iframe_payload_in_hr_field_is_rejected` | Lulus |
| Broken Authentication | TC-BA-01 | Password tersimpan dalam bentuk hash PBKDF2 | `test_tc_ba_01_password_is_hashed_with_pbkdf2_not_plaintext` | Lulus |
| Broken Authentication | TC-BA-02 | Lockout setelah lima percobaan gagal | `test_tc_ba_02_login_is_locked_after_five_failed_attempts` | Lulus |
| Broken Authentication | TC-BA-03 | Session lama tidak berlaku setelah logout | `test_tc_ba_03_old_session_cookie_cannot_access_dashboard_after_logout` | Lulus |
| Broken Authentication | TC-BA-04 | Halaman HR/payroll terlindungi dari akses tanpa login | `test_tc_ba_04_protected_hr_pages_redirect_without_login` | Lulus |
| Broken Authentication | TC-BA-05 | Error login bersifat generik | `test_tc_ba_05_login_error_is_generic_for_unknown_and_known_user` | Lulus |
| CSRF | TC-CSRF-01 | Semua form write menampilkan CSRF token | `test_tc_csrf_01_all_write_forms_render_csrf_token` | Lulus |
| CSRF | TC-CSRF-02 | Token CSRF invalid ditolak dan data tidak berubah | `test_tc_csrf_02_invalid_token_is_rejected_and_employee_data_unchanged` | Lulus |
| CSRF | TC-CSRF-03 | Cross-origin POST ditolak | `test_tc_csrf_03_cross_origin_post_without_token_is_rejected` | Lulus |
| CSRF | TC-CSRF-04 | Update salary/position tanpa CSRF valid ditolak | `test_tc_csrf_04j_hr_salary_or_position_update_without_valid_csrf_is_rejected` | Lulus |
| Business Security | TC-PAY-01 | Formula payroll menolak potongan tidak valid | `test_payroll_formula_rejects_negative_or_excessive_deduction` | Lulus |
| Authorization | TC-AUTHZ-01 | Karyawan hanya melihat slip gaji sendiri yang approved/paid | `test_least_privilege_employee_only_sees_approved_or_paid_own_payslips` | Lulus |
| Authorization | TC-AUTHZ-02 | Manajer hanya melihat bawahan langsung | `test_least_privilege_manager_only_sees_direct_reports` | Lulus |

### 5.5 Analisis Unit Testing per Area

#### 5.5.1 Code Injection Prevention

Fungsi yang diuji adalah validasi dan sanitasi input pada `EmployeeProfileForm`, `AttendanceNoteForm`, dan proses render template. Payload seperti `<script>`, `<iframe>`, tag HTML, dan `{{7*7}}` digunakan untuk menguji apakah aplikasi mengeksekusi atau menampilkan input berbahaya.

Hasilnya, input berbahaya ditolak atau disanitasi sebelum disimpan. Template payload tidak dievaluasi sebagai kode. Hal ini menunjukkan bahwa aplikasi tidak memproses input pengguna sebagai kode aktif.

#### 5.5.2 Broken Authentication Mitigation

Fungsi yang diuji mencakup password hashing, lockout login, generic error message, dan invalidasi session setelah logout. Test membuktikan bahwa password tidak disimpan dalam plaintext, lockout aktif setelah lima percobaan login gagal, dan session lama tidak dapat digunakan kembali setelah logout.

#### 5.5.3 CSRF Protection

Fungsi yang diuji mencakup keberadaan token CSRF pada form write dan penolakan request POST tanpa token valid. Test menggunakan `Client(enforce_csrf_checks=True)` agar pengecekan CSRF tidak dilewati oleh test client.

Hasilnya, request POST tanpa token valid menghasilkan HTTP 403 dan data tidak berubah.

#### 5.5.4 SQL Injection Prevention

Fungsi yang diuji mencakup login, search karyawan, dan white-box inspection source code. Payload SQL injection tidak berhasil login, tidak menampilkan hash password, tidak menimbulkan error database, dan tidak membuka seluruh data karyawan.

Aplikasi menggunakan Django ORM dan tidak memakai raw SQL yang menggabungkan input pengguna secara langsung.

## 6. Laporan Pentesting

### 6.1 Tujuan Pentesting

Pentesting dilakukan untuk mengevaluasi keamanan aplikasi dari sudut pandang attacker. Pengujian tidak hanya memeriksa fungsi keamanan secara unit, tetapi juga menguji perilaku aplikasi melalui request HTTP nyata.

### 6.2 Scope Pentesting

Target pengujian:

```text
http://127.0.0.1:8000
```

Endpoint utama yang diuji:

| Endpoint | Fungsi | Risiko utama |
|---|---|---|
| `/login/` | Login | Broken authentication, brute force, SQL injection login bypass |
| `/dashboard/` | Dashboard user | Unauthorized access |
| `/employees/` | Daftar karyawan | SQL injection, information disclosure, broken authorization |
| `/employees/<id>/edit/` | Update data karyawan | CSRF, code injection, salary manipulation |
| `/attendance/check-in/` | Absensi masuk | CSRF, invalid input |
| `/attendance/check-out/` | Absensi keluar | CSRF, invalid workflow |
| `/payroll/` | Daftar payroll | Broken authorization, information disclosure |
| `/payroll/new/` | Buat payroll | Broken authorization, payroll fraud |
| `/payroll/<id>/update/` | Update payroll | CSRF, payroll manipulation |
| `/payroll/<id>/approve/` | Approval payroll | Authorization bypass, ghost employee fraud |
| `/audit/` | Audit log | Information disclosure, repudiation risk |

### 6.3 Tools dan Command Pengujian

Tool utama yang digunakan pada deliverable ini:

1. Django Test Runner untuk unit testing.
2. Python `requests` untuk active HTTP testing.
3. Python `socket` untuk port scanning sederhana.
4. Browser DevTools untuk memeriksa token CSRF, cookie, dan response header.

Command pengujian manual yang sudah disiapkan:

```bash
python docs/pentest-logs/manual_pentest.py
```

Lokasi hasil pengujian:

```text
docs/pentest-logs/tugas4_manual_pentest_result.txt
```

Command yang dapat digunakan untuk reproduksi tambahan dengan Nmap:

```bash
nmap -sV -p 8000 127.0.0.1
```

Command yang dapat digunakan untuk reproduksi tambahan dengan OWASP ZAP Baseline Scan melalui Docker:

```bash
docker run --rm -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t http://host.docker.internal:8000 -r zap_report.html
```

Catatan: hasil aktual yang dilampirkan pada repository ini berasal dari script manual `manual_pentest.py` agar pengujian tetap dapat direproduksi tanpa instalasi Nmap atau ZAP.

### 6.4 Tahap 1 - Passive & Active Reconnaissance

Tujuan tahap ini adalah mengenali service, endpoint, header keamanan, dan perilaku awal aplikasi.

Hasil ringkas:

| Item | Hasil |
|---|---|
| Target | `http://127.0.0.1:8000` |
| Port terbuka pada rentang 7995 sampai 8005 | `8000` |
| Server | `WSGIServer/0.2 CPython/3.13.5` |
| Halaman publik `/` | HTTP 200 |
| `/dashboard/` tanpa login | HTTP 302 ke login |
| `/employees/` tanpa login | HTTP 302 ke login |
| `/payroll/` tanpa login | HTTP 302 ke login |
| `/audit/` tanpa login | HTTP 302 ke login |
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `same-origin` |

Interpretasi: aplikasi sudah menutup endpoint sensitif dari akses anonim. Header keamanan dasar sudah aktif. Namun, pada mode development, header server masih menampilkan informasi runtime. Pada deployment produksi, informasi ini sebaiknya diminimalkan melalui reverse proxy.

### 6.5 Tahap 2 - Threat Modeling

Threat modeling dilakukan dengan memetakan aset, aktor, attack surface, dan potensi ancaman.

Aset penting:

| Aset | Alasan penting |
|---|---|
| Data karyawan | Berisi identitas, NIK, email, telepon, alamat, status kerja |
| Data payroll | Berisi gaji pokok, tunjangan, potongan, total gaji, rekening |
| Data absensi | Berhubungan dengan kehadiran dan status kerja |
| Session user | Menentukan identitas dan role pengguna aktif |
| Audit log | Menjadi bukti akuntabilitas dan investigasi |

Aktor dan ancaman:

| Aktor | Potensi ancaman | Kontrol yang diuji |
|---|---|---|
| Pengguna anonim | Login bypass, brute force, akses halaman sensitif | Authentication, lockout, redirect login |
| Karyawan | Mengakses payroll atau data karyawan lain | RBAC, least privilege |
| Manajer | Melihat data di luar bawahan langsung | Filter data berbasis manager |
| HR | Mengubah data karyawan atau payroll tanpa jejak | Form validation, CSRF, audit log |
| Finance | Approve payroll yang tidak valid | Validasi status karyawan dan rekening |
| Attacker eksternal | SQL injection, XSS, CSRF, enumeration | ORM, sanitasi, CSRF token, generic error |

Mapping STRIDE ringkas:

| STRIDE | Ancaman | Contoh target | Mitigasi |
|---|---|---|---|
| Spoofing | Login sebagai user lain | `/login/` | Password hashing, session management, lockout |
| Tampering | Manipulasi gaji atau rekening | `/employees/<id>/edit/`, `/payroll/<id>/update/` | CSRF, role check, audit log, validasi rekening |
| Repudiation | Menyangkal perubahan data | Aksi HR/Finance | Audit log |
| Information Disclosure | Membaca data karyawan atau payroll tidak sah | `/employees/`, `/payroll/`, `/audit/` | Login required, RBAC, least privilege |
| Denial of Service | Percobaan login masif | `/login/` | Lockout setelah 5 percobaan gagal |
| Elevation of Privilege | Karyawan membuka fitur HR/Finance | `/payroll/new/`, `/audit/` | Decorator role-based access |

### 6.6 Tahap 3 - Scanning & Enumeration

Scanning dilakukan melalui request HTTP pada endpoint penting. Hasil utama:

| Pengujian | Payload atau aksi | Hasil | Status |
|---|---|---|---|
| Endpoint sensitif tanpa login | GET `/dashboard/`, `/employees/`, `/payroll/`, `/audit/` | HTTP 302 ke login | Aman |
| Port scan sederhana | Rentang 7995 sampai 8005 | Hanya port 8000 terbuka | Aman untuk lokal |
| Security header | GET `/` dan `/login/` | `X-Frame-Options: DENY`, `nosniff`, `same-origin` | Aman dasar |
| Login SQLi | Username `' OR '1'='1' --` | Tidak login, HTTP 200 tanpa redirect dashboard | Aman |
| Brute force | 6 percobaan gagal | Percobaan ke-6 HTTP 403 | Aman |
| Search SQLi | `EMP001' OR '1'='1' --` | Hanya data target yang relevan, tidak membuka seluruh data | Aman |
| UNION SQLi | `' UNION SELECT username,password,NULL FROM auth_user --` | Tidak menampilkan hash password atau error database | Aman |
| Template injection | `{{7*7}}` | Tidak dievaluasi menjadi `49` | Aman |
| XSS payload | `<script>alert(1)</script>` | Tidak dirender sebagai script aktif | Aman |
| CSRF | POST tanpa token valid | HTTP 403 | Aman |
| Cross-origin POST | Header `Origin: http://evil.example` | HTTP 403 | Aman |
| Authorization karyawan | GET `/employees/`, `/audit/`, `/payroll/new/` | HTTP 403 | Aman |

### 6.7 Tahap 4 - Exploitation & Testing

#### 6.7.1 SQL Injection Login Bypass

Payload:

```text
username = ' OR '1'='1' --
password = bebas
```

Hasil: login gagal. Response tetap HTTP 200 pada halaman login, tidak ada redirect ke dashboard, dan session tidak menjadi authenticated.

Kesimpulan: login tidak membangun query SQL manual dari input pengguna. Authentication memakai mekanisme Django.

#### 6.7.2 SQL Injection pada Search Karyawan

Payload:

```text
EMP001' OR '1'='1' --
```

Hasil: aplikasi mengekstrak pola ID karyawan aman, lalu melakukan filtering dengan Django ORM. Payload tidak menyebabkan seluruh data karyawan terbuka.

Kesimpulan: mitigasi SQL injection efektif karena input tidak digabungkan ke raw SQL.

#### 6.7.3 Code Injection dan XSS

Payload:

```html
<script>alert(1)</script>
<iframe src="javascript:alert('xss')"></iframe>
{{7*7}}
```

Hasil: payload ditolak, disanitasi, atau tidak dievaluasi. Tidak ada eksekusi script di sisi browser dan tidak ada evaluasi template expression.

Kesimpulan: kombinasi validasi form, sanitasi input, dan autoescape Django mengurangi risiko code injection dan reflected/stored XSS.

#### 6.7.4 Broken Authentication

Skenario:

1. Melakukan enam kali login gagal.
2. Memeriksa apakah akun atau kombinasi username dan IP dikunci.
3. Memastikan pesan error tidak membocorkan apakah username salah atau password salah.

Hasil: setelah lima percobaan gagal, percobaan berikutnya menghasilkan HTTP 403. Pesan error tetap generik.

Kesimpulan: kontrol lockout dan generic error message bekerja.

#### 6.7.5 CSRF

Skenario:

1. Login sebagai HR.
2. Mengirim POST ke endpoint update karyawan tanpa token CSRF.
3. Mengirim POST dari origin eksternal yang tidak dipercaya.

Hasil: kedua request ditolak dengan HTTP 403 dan data tidak berubah.

Kesimpulan: perlindungan CSRF bekerja pada endpoint write.

#### 6.7.6 Authorization dan Least Privilege

Skenario:

1. Login sebagai `employee1`.
2. Mencoba membuka `/employees/`, `/audit/`, dan `/payroll/new/`.

Hasil: seluruh endpoint mengembalikan HTTP 403.

Kesimpulan: karyawan tidak dapat mengakses fitur HR, Finance, atau audit log.

### 6.8 Tahap 5 - Reporting & Remediation

#### 6.8.1 Ringkasan Temuan

| ID | Temuan | Severity | Status | Bukti |
|---|---|---|---|---|
| F-01 | Endpoint sensitif tanpa login diarahkan ke login | Info | Aman | HTTP 302 |
| F-02 | Login bypass SQL injection gagal | Low | Aman | HTTP 200 tanpa session login |
| F-03 | Brute force login dikunci setelah 5 gagal | Low | Aman | Percobaan ke-6 HTTP 403 |
| F-04 | Search SQLi tidak membocorkan password hash | Low | Aman | Tidak ada `pbkdf2_sha256` pada response |
| F-05 | CSRF token invalid atau kosong ditolak | Low | Aman | HTTP 403 |
| F-06 | Karyawan tidak bisa mengakses fitur HR/Finance/Audit | Low | Aman | HTTP 403 |
| F-07 | Mode development menampilkan identitas server | Low | Perlu hardening produksi | Header `Server: WSGIServer/0.2 CPython/3.13.5` |
| F-08 | HSTS belum relevan pada HTTP lokal | Low | Perlu hardening produksi | HTTPS belum digunakan |

#### 6.8.2 Rekomendasi Perbaikan

| Area | Rekomendasi |
|---|---|
| Deployment | Gunakan `DEBUG=False`, reverse proxy, HTTPS, dan konfigurasi secure cookie pada production |
| Header keamanan | Tambahkan `Strict-Transport-Security` saat HTTPS aktif dan pertimbangkan Content Security Policy |
| Audit log | Buat audit log append-only atau kirim ke storage/log server terpisah agar tidak mudah dimodifikasi |
| Monitoring | Tambahkan alert untuk login gagal berulang, akses 403 masif, dan perubahan payroll besar |
| Secret management | Pastikan `SECRET_KEY`, kredensial, dan konfigurasi sensitif tidak masuk repository |
| Dependency security | Gunakan dependency pinning dan pemeriksaan berkala terhadap versi package |
| Database | Batasi permission file SQLite dan lakukan backup berkala |
| Admin panel | Batasi akses `/admin/` pada jaringan internal atau gunakan MFA untuk admin produksi |

### 6.9 Kesimpulan Pentesting

Berdasarkan pengujian lokal, aplikasi tidak berhasil dieksploitasi melalui empat kategori utama yang diwajibkan, yaitu code injection, broken authentication, CSRF, dan SQL/database injection. Aplikasi juga sudah menerapkan least privilege untuk role karyawan, manajer, HR, Finance, dan admin.

Temuan yang tersisa lebih bersifat deployment hardening, bukan kelemahan eksploitasi langsung pada logic aplikasi.

## 7. Laporan User Acceptance Testing

### 7.1 Tujuan UAT

User Acceptance Testing dilakukan untuk memastikan aplikasi dapat digunakan oleh role utama sesuai kebutuhan bisnis HR & Payroll. Pengujian berfokus pada apakah fitur dapat dijalankan, apakah akses sesuai role, dan apakah hasil proses sesuai ekspektasi pengguna.

### 7.2 Peserta UAT

| Role penguji | Akun demo | Fokus pengujian |
|---|---|---|
| Karyawan | `employee1` | Profil, absensi, slip gaji |
| Manajer | `manager1` | Data bawahan dan absensi tim |
| HR | `hr1` | Master data karyawan dan draft payroll |
| Finance | `finance1` | Approval payroll |
| Admin | `admin1` | Validasi akses administratif |

### 7.3 Skenario UAT

| UAT-ID | Role | Skenario | Langkah ringkas | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| UAT-01 | Karyawan | Login dan melihat dashboard | Login sebagai `employee1` | Dashboard karyawan terbuka | Dashboard terbuka | Lulus |
| UAT-02 | Karyawan | Check in absensi | Buka dashboard atau attendance, isi catatan, submit check in | Absensi tercatat | Absensi tercatat atau muncul pesan sudah check in jika data hari ini ada | Lulus |
| UAT-03 | Karyawan | Check out absensi | Submit check out setelah check in | Check out tercatat | Check out tercatat jika sudah check in | Lulus |
| UAT-04 | Karyawan | Melihat slip gaji | Buka payroll list | Hanya slip gaji milik sendiri dengan status approved/paid yang tampil | Data dibatasi sesuai aturan | Lulus |
| UAT-05 | Karyawan | Mencoba akses data karyawan | Buka `/employees/` | Akses ditolak | HTTP 403 | Lulus |
| UAT-06 | Manajer | Melihat bawahan langsung | Login sebagai `manager1`, buka employee list | Hanya bawahan langsung tampil | Data bawahan langsung tampil | Lulus |
| UAT-07 | HR | Membuat data karyawan | Login sebagai `hr1`, buka employee create, isi form valid | Data karyawan tersimpan | Data tersimpan jika input valid | Lulus |
| UAT-08 | HR | Mengubah data karyawan | Login sebagai `hr1`, ubah posisi atau status karyawan | Data berubah dan tercatat pada audit log | Data berubah dan audit log dibuat | Lulus |
| UAT-09 | HR | Membuat draft payroll | Login sebagai `hr1`, isi form payroll | Draft payroll tersimpan dan total dihitung | Payroll tersimpan dan total dihitung | Lulus |
| UAT-10 | Finance | Approve payroll | Login sebagai `finance1`, buka detail payroll, approve | Payroll berubah menjadi approved jika rekening dan status karyawan valid | Payroll approved | Lulus |
| UAT-11 | Finance | Menolak payroll tidak valid secara sistem | Ubah data rekening payroll tidak cocok, lalu approve | Approval ditolak | Approval ditolak oleh validasi | Lulus |
| UAT-12 | HR/Admin | Melihat audit log | Login sebagai HR/admin, buka `/audit/` | Audit log tampil | Audit log tampil | Lulus |

### 7.4 Kriteria Penerimaan UAT

| Kriteria | Status |
|---|---|
| Semua role dapat login menggunakan akun demo yang sesuai | Terpenuhi |
| Karyawan hanya dapat mengakses data miliknya sendiri | Terpenuhi |
| Manajer hanya melihat bawahan langsung | Terpenuhi |
| HR dapat mengelola data karyawan dan draft payroll | Terpenuhi |
| Finance dapat melakukan approval payroll sesuai validasi | Terpenuhi |
| Endpoint sensitif tidak terbuka untuk role yang tidak berwenang | Terpenuhi |
| Aksi penting dicatat pada audit log | Terpenuhi |

### 7.5 Kesimpulan UAT

Aplikasi memenuhi kebutuhan fungsional utama untuk skenario HR & Payroll. Setiap role dapat menjalankan aktivitas yang relevan dan tidak memperoleh akses di luar kewenangannya. Dengan demikian, aplikasi dapat diterima untuk kebutuhan demonstrasi tugas kelompok.

## 8. Laporan Operational Acceptance Testing

### 8.1 Tujuan OAT

Operational Acceptance Testing dilakukan untuk memastikan aplikasi dapat dijalankan, dipelihara, dan diamankan secara operasional pada lingkungan lokal maupun ketika dipersiapkan menuju deployment.

### 8.2 Skenario OAT

| OAT-ID | Area | Skenario | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| OAT-01 | Instalasi | Instal dependency dari `requirements.txt` | Dependency terpasang | Berhasil pada environment yang sesuai | Lulus |
| OAT-02 | Database | Menjalankan migrasi | Tabel database terbentuk | `python manage.py migrate` berhasil | Lulus |
| OAT-03 | Seed data | Membuat akun dan data demo | Akun demo tersedia | `python manage.py seed_demo` berhasil | Lulus |
| OAT-04 | Startup | Menjalankan server lokal | Aplikasi aktif di port 8000 | Server berjalan di `127.0.0.1:8000` | Lulus |
| OAT-05 | Health check | Membuka `/` dan `/login/` | HTTP 200 | HTTP 200 | Lulus |
| OAT-06 | Access control | Membuka endpoint sensitif tanpa login | Redirect ke login | HTTP 302 | Lulus |
| OAT-07 | Logging | Aksi login, logout, update, approval tercatat | Audit log bertambah | Audit log tersedia | Lulus |
| OAT-08 | Backup | Backup SQLite | File database dapat disalin | Perlu prosedur rutin produksi | Lulus dengan catatan |
| OAT-09 | Security config | Cookie dan header keamanan dasar | `HttpOnly`, SameSite, X-Frame-Options, nosniff aktif | Konfigurasi aktif | Lulus |
| OAT-10 | Production readiness | HTTPS, HSTS, reverse proxy | Aktif pada deployment produksi | Belum relevan pada server lokal HTTP | Lulus dengan catatan |

### 8.3 Checklist Operasional

| Komponen | Kondisi saat ini | Rekomendasi produksi |
|---|---|---|
| Database | SQLite lokal | Backup rutin, permission file ketat, enkripsi disk bila diperlukan |
| Static file | Dilayani lokal saat `DEBUG=True` | Gunakan `collectstatic` dan web server produksi |
| Secret key | Dibaca dari `.env` dengan fallback lokal | Wajib gunakan secret unik di `.env` produksi |
| Debug mode | Default lokal `True` | Wajib `DEBUG=False` pada produksi |
| HTTPS | Belum digunakan pada lokal | Wajib HTTPS untuk produksi |
| Session cookie | `HttpOnly`, `SameSite=Lax`, secure mengikuti `DEBUG` | Pastikan `SESSION_COOKIE_SECURE=True` saat HTTPS |
| CSRF cookie | `SameSite=Lax`, secure mengikuti `DEBUG` | Pastikan `CSRF_COOKIE_SECURE=True` saat HTTPS |
| Audit log | Tersimpan di database | Kirim ke log server atau storage append-only |
| Monitoring | Belum ada dashboard monitoring | Tambahkan alert login gagal dan perubahan payroll |

### 8.4 Kesimpulan OAT

Aplikasi layak dijalankan pada lingkungan lokal untuk kebutuhan demonstrasi dan pengujian. Untuk produksi, aplikasi masih memerlukan hardening deployment, terutama HTTPS, HSTS, reverse proxy, monitoring, backup, dan pengelolaan secret yang lebih ketat.

