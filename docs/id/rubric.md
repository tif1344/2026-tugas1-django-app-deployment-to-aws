# Rubrik penilaian

> 🇬🇧 English version: [../en/rubric.md](../en/rubric.md)

Level dinilai secara berurutan. Sebuah level hanya dihitung jika level sebelumnya berjalan sepenuhnya. Nilai akhir maksimal **100**.

## Level 1 — VPC + EC2 (maks 60)

| Kriteria | Poin | Nilai penuh jika |
|---|---|---|
| Desain VPC | 15 | VPC sendiri `10.0.0.0/16` dengan DNS hostnames aktif; 2 subnet publik + 2 subnet privat di 2 AZ; IGW terpasang; route table publik dengan `0.0.0.0/0 → IGW` hanya untuk subnet publik; route table privat hanya `local` |
| Security group | 10 | Hanya port 80 dari mana saja dan port 22 hanya dari IP anggota (masing-masing `/32`); tidak ada port lain yang terbuka |
| Konfigurasi server | 15 | Elastic IP; Gunicorn berjalan di bawah systemd dan tetap hidup setelah reboot; Nginx meneruskan ke `127.0.0.1:8000` dan menyajikan `/static/` serta `/media/` |
| Aplikasi berjalan | 10 | Tampilan website bergaya, login admin berhasil, gambar unggahan tampil, formulir kontak berfungsi, `DEBUG=false`, `/status/` menunjukkan Level 1, tagline memuat nama kelompok |
| Laporan & pertanyaan | 10 | Diagram arsitektur benar, bukti lengkap, jawaban menunjukkan pemahaman |

## Level 2 — S3 (+20, maks 80)

| Kriteria | Poin | Nilai penuh jika |
|---|---|---|
| Bucket & policy | 5 | ACL nonaktif; bucket policy memberi `s3:GetObject` hanya untuk `static/*` dan `media/*`; melihat daftar isi bucket ditolak |
| IAM role | 5 | Role terpasang di instance dengan policy yang dibatasi pada bucket; **tidak ada access key di mana pun** |
| Berjalan di S3 | 7 | `collectstatic` ke S3; media Level 1 sudah disinkronkan; unggahan baru masuk ke S3; page source menunjukkan URL S3; `/status/` menunjukkan Level 2 |
| Laporan & pertanyaan | 3 | Diagram diperbarui, bukti, jawaban |

## Level 3 — RDS (+20, maks 100)

| Kriteria | Poin | Nilai penuh jika |
|---|---|---|
| Penempatan RDS | 6 | PostgreSQL dalam DB subnet group berisi 2 subnet privat; *Publicly accessible: No* |
| Rantai security group | 4 | `db-sg` mengizinkan 5432 **hanya** dari `web-sg` |
| Migrasi data | 6 | Data Level 1 (pesan kontak, berita, user admin) ada di RDS; koneksi memakai `sslmode=require`; `/status/` menunjukkan Level 3 |
| Laporan & pertanyaan | 4 | Diagram diperbarui, uji dari laptop yang membuktikan RDS privat, jawaban |

## Bonus (maks +10, nilai akhir tetap maksimal 100)

| Tugas | Poin |
|---|---|
| HTTPS dengan (sub)domain sendiri dan Let's Encrypt (`certbot --nginx`), plus `SECURE_COOKIES=true` | +4 |
| CloudFront di depan bucket S3 (`AWS_S3_CUSTOM_DOMAIN`), dengan bucket tidak lagi publik (Origin Access Control) | +4 |
| Port 22 ditutup; server dikelola lewat SSM Session Manager atau EC2 Instance Connect Endpoint | +3 |
| S3 Gateway VPC Endpoint, dengan bukti lalu lintas S3 melewatinya | +2 |
| CloudWatch alarm (CPU EC2 atau free storage RDS) dengan notifikasi email | +2 |

## Pengurangan nilai

| Masalah | Poin |
|---|---|
| AWS access key ditemukan di server, di `.env`, atau terlihat di laporan/video | −10 |
| SSH (22) atau PostgreSQL (5432) terbuka untuk `0.0.0.0/0` | −5 per port |
| Nama resource tidak memuat nama kelompok | −5 |
| Anggota kelompok berbagi login root account, bukan memakai IAM user masing-masing | −5 |
| Password atau `SECRET_KEY` terlihat di laporan/video | −5 |
| Terlambat mengumpulkan | sesuai kebijakan mata kuliah |
| Instance ID, bucket, IP, atau isi laporan sama dengan kelompok lain | nilai 0 untuk kedua kelompok |
| Anggota tanpa kontribusi yang tercatat | nilai anggota tersebut dikurangi, sesuai pertimbangan dosen |
