# Level 2 — EC2 + S3 untuk file statis dan media

> 🇬🇧 English version: [../en/level-2-s3.md](../en/level-2-s3.md)

**Prasyarat:** Level 1 sudah berjalan.

**Tujuan:** CSS, JavaScript, gambar, dan dokumen unggahan disimpan dan disajikan dari bucket S3, bukan dari disk EC2. Instance mendapat izin menulis ke bucket melalui **IAM role**. Tidak ada access key di mana pun.

```
   Browser ──HTML──▶ EC2 (Nginx + Gunicorn + SQLite)
      │                     │  upload / collectstatic
      │                     │  (kredensial dari IAM role)
      │                     ▼
      └──gambar, CSS──▶ Bucket S3 pcm-<kelompok>-assets
                          ├── static/   (collectstatic)
                          └── media/    (unggahan admin)
```

Django tetap membuat halaman HTML, tetapi setiap `src="..."` dan `href="..."` untuk file kini mengarah ke `https://pcm-<kelompok>-assets.s3.ap-southeast-3.amazonaws.com/...`. Browser mengunduh file-file itu langsung dari S3.

---

## Langkah 1 — Buat bucket

**S3 → Create bucket** (di region yang sama dengan EC2):

- Bucket name: `pcm-<kelompok>-assets`. Nama bucket berlaku global; tambahkan akhiran jika nama sudah dipakai.
- Object Ownership: **ACLs disabled (Bucket owner enforced)**
- Block Public Access: **hapus centang "Block all public access"** dan centang pernyataan persetujuannya. Kita hanya mengizinkan *pembacaan* publik untuk dua folder, lewat bucket policy di langkah berikutnya.
- Versioning: nonaktif. Default encryption: SSE-S3 (bawaan).

## Langkah 2 — Bucket policy (baca publik hanya untuk `static/` dan `media/`)

Bucket → *Permissions → Bucket policy* → tempel isi [`deploy/aws/s3-bucket-policy.json`](../../deploy/aws/s3-bucket-policy.json) dan ganti `BUCKET_NAME` dengan nama bucket Anda.

Policy ini mengizinkan siapa pun **membaca** objek di `static/` dan `media/`. Tidak ada yang bisa melihat daftar isi bucket, dan tidak ada yang bisa menulis ke bucket kecuali role EC2.

## Langkah 3 — IAM role untuk instance EC2

1. **IAM → Roles → Create role** → Trusted entity: *AWS service* → Use case: **EC2** → Next.
2. Lewati managed policy → beri nama `pcm-<kelompok>-ec2-s3-role` → Create.
3. Buka role tersebut → *Add permissions → Create inline policy* → JSON → tempel [`deploy/aws/ec2-s3-role-policy.json`](../../deploy/aws/ec2-s3-role-policy.json), ganti `BUCKET_NAME`, beri nama `pcm-s3-access`.
4. **EC2 → instance Anda → Actions → Security → Modify IAM role** → pilih `pcm-<kelompok>-ec2-s3-role`.

Di laporan, jelaskan apa yang diizinkan setiap statement dalam policy, dan mengapa role tidak diberi izin lebih dari itu (*least privilege*).

## Langkah 4 — Cek role dari dalam instance

```bash
sudo snap install aws-cli --classic
echo "export AWS_DEFAULT_REGION=ap-southeast-3" >> ~/.bashrc   # Jakarta region opt-in; CLI harus diberi tahu region-nya
source ~/.bashrc
aws sts get-caller-identity        # "Arn" harus memuat assumed-role/<nama role Anda>
aws s3 ls s3://pcm-<kelompok>-assets    # tidak error (output kosong tidak masalah)
```

Tidak ada `aws configure` dan tidak ada key. CLI, sama seperti boto3 di dalam Django, mengambil kredensial sementara dari *instance metadata service*.

## Langkah 5 — Pindahkan file media lama

Gambar yang dibuat di Level 1 masih ada di `/srv/pcm-website/app/media/`. Salin ke bucket dengan struktur folder yang sama:

```bash
cd /srv/pcm-website/app
aws s3 sync media/ s3://pcm-<kelompok>-assets/media/
```

## Langkah 6 — Alihkan Django ke S3

```bash
cd /srv/pcm-website/app
cp .env .env.level1.bak
nano .env
```

Pertahankan `SECRET_KEY`, `ALLOWED_HOSTS`, dan `CSRF_TRUSTED_ORIGINS` Anda. Ubah atau tambahkan baris berikut (lihat [`deploy/env/level2.env.example`](../../deploy/env/level2.env.example)):

```ini
USE_S3=true
AWS_STORAGE_BUCKET_NAME=pcm-<kelompok>-assets
AWS_S3_REGION_NAME=ap-southeast-3
```

Unggah file statis ke S3, lalu restart:

```bash
uv run python manage.py collectstatic --noinput     # mengunggah ~130 file ke s3://.../static/
sudo systemctl restart pcm
```

Tidak ada file Python yang diubah. [`app/pcm/settings.py`](../../app/pcm/settings.py) membaca `USE_S3` dan mengganti *storage backend*. Baca blok `USE_S3` dan bersiaplah menjelaskannya.

## Langkah 7 — Verifikasi

1. `http://<EIP>/status/` menampilkan **Level 2 terdeteksi**, `S3Storage`, nama bucket Anda, serta URL S3 untuk `STATIC_URL` dan `MEDIA_URL`.
2. Di beranda, klik kanan → *View page source*. Stylesheet dan gambar kini dimuat dari `...s3....amazonaws.com`.
3. Di admin, unggah gambar baru (mis. *Berita* baru). Gambar tampil di website, dan di konsol S3 pada `media/posts/<tahun>/<bulan>/`. Pastikan tidak ada file baru di `/srv/pcm-website/app/media/`.
4. Halaman admin tetap bergaya, karena CSS-nya juga berasal dari S3.
5. Buka URL akar bucket, misalnya `https://pcm-<kelompok>-assets.s3.ap-southeast-3.amazonaws.com/`, di browser. Hasilnya harus **AccessDenied**, karena melihat daftar isi bucket tidak diizinkan. File satuan di `static/` dan `media/` harus bisa dibuka.

## Bukti (untuk laporan)

- [ ] Tab *Permissions* bucket: pengaturan Block Public Access dan bucket policy
- [ ] Tampilan *Objects* bucket yang menunjukkan folder `static/` dan `media/`
- [ ] IAM role beserta trust relationship dan inline policy-nya
- [ ] Detail instance EC2 yang menunjukkan IAM role terpasang
- [ ] Output `aws sts get-caller-identity` di instance
- [ ] Page source yang menunjukkan URL S3, dan halaman `/status/`
- [ ] Objek S3 yang Anda unggah lewat admin

## Pertanyaan

1. Mengapa IAM role lebih aman daripada menaruh `AWS_ACCESS_KEY_ID` dan `AWS_SECRET_ACCESS_KEY` di `.env`?
2. Bucket policy hanya mengizinkan `s3:GetObject` untuk `static/*` dan `media/*`. Apa yang berubah jika diizinkan untuk `arn:aws:s3:::pcm-<kelompok>-assets/*`? Bagaimana jika `s3:*`?
3. Sebutkan dua keuntungan menyajikan file dari S3 dibanding dari disk EC2, dengan membayangkan **dua atau lebih** instance EC2 di belakang load balancer.
4. Bagian aplikasi apa yang masih tersimpan hanya di disk EC2 setelah Level 2?

➡️ Berikutnya: [Level 3 — RDS](level-3-rds.md)
