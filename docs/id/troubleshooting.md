# Troubleshooting & cleanup

> 🇬🇧 English version: [../en/troubleshooting.md](../en/troubleshooting.md)

Sebelum yang lain, periksa log:

```bash
sudo systemctl status pcm            # apakah Gunicorn berjalan?
journalctl -u pcm -n 50 --no-pager   # error Django/Gunicorn
sudo tail -n 50 /var/log/nginx/error.log
```

Setiap kali `.env` diubah, jalankan `sudo systemctl restart pcm`.

## Umum / Level 1

| Gejala | Kemungkinan penyebab | Solusi |
|---|---|---|
| SSH: `Connection timed out` | Rule SG port 22 memakai IP lama; tidak ada route ke IGW; tidak ada IP publik | Perbarui rule SSH ke *My IP*; pastikan `public-rt` punya `0.0.0.0/0 → igw` dan terasosiasi dengan subnet; pastikan Elastic IP terpasang |
| SSH: `Permission denied (publickey)` | Key atau user salah | User-nya `ubuntu`; jalankan `chmod 400` pada `.pem`; pakai key yang dipilih saat launch |
| Website sama sekali tidak bisa diakses | SG tidak membuka port 80; Nginx mati; Anda mengetik `https://` | Tambahkan HTTP 80; `sudo systemctl status nginx`; gunakan `http://` |
| Muncul halaman "Welcome to nginx" | Site default masih aktif | `sudo rm /etc/nginx/sites-enabled/default && sudo systemctl reload nginx` |
| **502 Bad Gateway** | Gunicorn tidak berjalan | `journalctl -u pcm -n 50`; penyebab umum: path salah di `pcm.service`, `uv sync` belum dijalankan, ada kesalahan penulisan di `.env` |
| **400 Bad Request** | Host tidak ada di `ALLOWED_HOSTS` | Masukkan IP atau domain persis seperti yang diketik di browser ke `ALLOWED_HOSTS`, lalu restart |
| `ImproperlyConfigured: SECRET_KEY must be set` | `.env` tidak ada atau `SECRET_KEY` kosong | `.env` harus berada di `/srv/pcm-website/app/` |
| **403 CSRF verification failed** saat login admin | Mengakses lewat host yang tidak ada di `CSRF_TRUSTED_ORIGINS` | Tambahkan `http://<EIP>` (lengkap dengan skema) ke `CSRF_TRUSTED_ORIGINS` |
| Website tampil tanpa CSS (Level 1) | `collectstatic` belum dijalankan, atau path Nginx salah | Jalankan `collectstatic`; pastikan path `alias` di `pcm.conf` diakhiri `/` |
| Gambar unggahan 404 (Level 1) | Nginx tidak bisa membaca `/srv/...`, atau path media salah | Cek `ls -l /srv/pcm-website/app/media`; aplikasi harus di `/srv`, bukan di `/home/ubuntu` |
| **413 Request Entity Too Large** | Ukuran unggahan melebihi batas Nginx | `client_max_body_size` di `pcm.conf` (bawaan 10M) |
| `uv: command not found` | Shell belum dimuat ulang setelah instal uv | `source ~/.local/bin/env` atau logout lalu login lagi |
| Jakarta tidak ada di daftar region, atau muncul error `OptInRequired` / "not enabled" | Region Jakarta belum diaktifkan untuk akun ini | Pemilik akun: *Account → AWS Regions → Asia Pacific (Jakarta) → Enable*, tunggu beberapa menit, lalu pilih **Jakarta** di pemilih region |
| Resource "hilang" dari konsol | Pemilih region berpindah dari Jakarta | Pilih **Asia Pacific (Jakarta)** di pemilih region kanan atas |

## Level 2

| Gejala | Kemungkinan penyebab | Solusi |
|---|---|---|
| `ImproperlyConfigured: USE_S3=true requires ...` | Nama bucket atau region tidak ada di `.env` | Isi `AWS_STORAGE_BUCKET_NAME` dan `AWS_S3_REGION_NAME` |
| `NoCredentialsError` / `Unable to locate credentials` | IAM role belum terpasang | Pasang role, tunggu ±30 detik, coba lagi |
| `AccessDenied` saat `collectstatic` atau unggah | Nama bucket di policy role salah, atau action-nya kurang | Bandingkan ARN di policy dengan nama bucket; uji dengan `aws s3 cp` |
| Gambar/CSS mendapat 403 di browser | Bucket policy tidak ada/salah, atau Block Public Access masih aktif | Pastikan resource di policy diakhiri `/static/*` dan `/media/*`; cek Block Public Access di level bucket **dan** level akun |
| `AccessControlListNotSupported` | Kode mencoba mengatur ACL | Biarkan `default_acl: None` (sudah diatur) dan *Bucket owner enforced* |
| Gambar lama hilang setelah beralih | Media Level 1 belum disalin | `aws s3 sync media/ s3://<bucket>/media/` |
| Region salah / `PermanentRedirect` | `AWS_S3_REGION_NAME` berbeda dengan region bucket | Pakai region yang tertera di properti bucket |

## Level 3

| Gejala | Kemungkinan penyebab | Solusi |
|---|---|---|
| `migrate` atau `psql` macet lalu timeout | `db-sg` tidak mengizinkan 5432 dari `web-sg`; RDS di VPC yang salah | Perbaiki inbound rule; cek VPC dan subnet group RDS |
| `could not translate host name` | Endpoint salah ketik; pengaturan DNS VPC nonaktif | Salin ulang endpoint; aktifkan DNS resolution dan DNS hostnames di VPC |
| `password authentication failed` | Password salah, atau ada karakter khusus di `DATABASE_URL` | Pakai huruf dan angka saja, atau lakukan URL-encode (`@` → `%40`, `#` → `%23`, `/` → `%2F`) |
| `database "pcm" does not exist` | Initial database name dibiarkan kosong | `psql "host=<ENDPOINT> dbname=postgres user=pcm_admin sslmode=require"` → `CREATE DATABASE pcm;` |
| `loaddata` gagal dengan `IntegrityError` / duplicate key | `loaddata` dijalankan dua kali, atau `seed_pcm` dijalankan ke RDS | `uv run python manage.py flush --noinput`, lalu `loaddata data.json` lagi |
| `/status/` menampilkan *Konfigurasi di luar level tugas* | Postgres terhubung tetapi `USE_S3` mati, atau host bukan RDS | Pastikan `.env` memuat pengaturan Level 2 dan Level 3 sekaligus |
| Login admin gagal setelah migrasi | Tabel `auth` ikut dikecualikan saat dump | Ulangi `dumpdata` persis seperti contoh (hanya `auth.permission` yang dikecualikan) |

---

## Cleanup

Lakukan **hanya setelah nilai Anda diumumkan**. Hapus dengan urutan berikut; beberapa resource menghalangi penghapusan resource lain.

1. **RDS:** hapus `pcm-<kelompok>-db` (hapus centang *Create final snapshot*, centang pernyataan persetujuan). Lalu hapus DB subnet group.
2. **S3:** *Empty* bucket, lalu *Delete*.
3. **EC2:** *terminate* `pcm-<kelompok>-web`.
4. **Elastic IP:** *Release*. Elastic IP yang tidak terpasang tetap ditagih.
5. **IAM:** hapus `pcm-<kelompok>-ec2-s3-role`, serta IAM user yang dibuat untuk anggota kelompok.
6. **Security group:** hapus `db-sg`, lalu `web-sg`.
7. **VPC:** hapus `pcm-<kelompok>-vpc`. Subnet, route table, dan IGW-nya ikut terhapus.
8. Cek **Billing → Bills** serta **EC2 → Volumes / Snapshots** untuk resource yang tersisa.
