# Level 3 — EC2 + S3 + RDS PostgreSQL

> 🇬🇧 English version: [../en/level-3-rds.md](../en/level-3-rds.md)

**Prasyarat:** Level 2 sudah berjalan.

**Tujuan:** database dipindah dari file SQLite di EC2 ke **Amazon RDS for PostgreSQL** di subnet privat. Database tidak bisa diakses dari internet, hanya dari security group web server. Semua data lama ikut pindah, termasuk pesan kontak yang Anda kirim di Level 1 dan akun admin Anda.

```
                Internet
                    │ :80
   ┌────────────────▼──────────── VPC ───────────────────────────────┐
   │  public-a                          private-a        private-b   │
   │  ┌──────────────────────┐ :5432   ┌──────────────────────────┐  │
   │  │ EC2 web server       │────────▶│ RDS PostgreSQL           │  │
   │  │ sg: web-sg           │         │ sg: db-sg                │  │
   │  └──────────┬───────────┘         │ (DB subnet group a + b)  │  │
   │             │                     └──────────────────────────┘  │
   └─────────────┼───────────────────────────────────────────────────┘
                 ▼
         S3 pcm-<kelompok>-assets
```

Setelah level ini, instance EC2 **tidak menyimpan state** apa pun. File ada di S3 dan data ada di RDS. Anda bisa men-*terminate* instance, membuat instance baru dengan kode dan `.env` yang sama, dan website akan kembali persis seperti semula.

---

## Langkah 1 — Security group database

Buat `pcm-<kelompok>-db-sg` di `pcm-<kelompok>-vpc`, dengan satu inbound rule:

| Type | Port | Source |
|---|---|---|
| PostgreSQL | 5432 | **`pcm-<kelompok>-web-sg`** (security group-nya, bukan rentang IP) |

Memakai security group sebagai source berarti "instance mana pun yang memiliki `web-sg`". Jika IP web server berubah, atau Anda menambah web server kedua, rule ini tetap berlaku.

## Langkah 2 — DB subnet group

**RDS → Subnet groups → Create**

- Nama: `pcm-<kelompok>-db-subnets`, VPC: `pcm-<kelompok>-vpc`
- Availability Zones: kedua AZ yang Anda pakai. Subnet: **hanya `private-a` dan `private-b`**.

## Langkah 3 — Buat instance RDS

**RDS → Create database**

- *Standard create* · Engine: **PostgreSQL** (versi terbaru yang tersedia, mis. 17.x)
- Template: **Free tier** (atau *Sandbox* / *Dev/Test* jika Free tier tidak muncul) · Deployment: **Single-AZ DB instance**
- DB instance identifier: `pcm-<kelompok>-db`
- Master username: `pcm_admin` · Credentials management: **Self managed**. Pilih password yang **hanya berisi huruf dan angka**, agar tidak perlu di-*escape* di URL.
- Instance class: `db.t3.micro` atau `db.t4g.micro` · Storage: gp3, 20 GiB, **storage autoscaling nonaktif**
- Connectivity:
  - Compute resource: **Don't connect to an EC2 compute resource**. Anda menghubungkannya sendiri lewat security group.
  - VPC: `pcm-<kelompok>-vpc` · DB subnet group: `pcm-<kelompok>-db-subnets`
  - **Public access: No**
  - VPC security group: pilih yang sudah ada → `pcm-<kelompok>-db-sg` (hapus `default`)
- Monitoring: matikan **Performance Insights** dan **Enhanced Monitoring**
- Additional configuration:
  - **Initial database name: `pcm`**. Tanpa ini, RDS tidak membuat database-nya.
  - Backup retention: 1 hari · Deletion protection: nonaktif (agar mudah dihapus nanti)

Pembuatan memakan waktu sekitar 10 menit. Setelah status *Available*, salin **Endpoint**-nya, mis. `pcm-<kelompok>-db.xxxxxxxx.ap-southeast-3.rds.amazonaws.com`.
## Langkah 4 — Uji koneksi dari EC2

```bash
sudo apt install -y postgresql-client
psql "host=<ENDPOINT> port=5432 dbname=pcm user=pcm_admin sslmode=require"
# masukkan password; Anda akan mendapat prompt  pcm=>  . Ketik \q untuk keluar.
```

Jika macet (*hang*), masalahnya ada di jaringan (security group atau subnet), bukan di Django. Lihat [troubleshooting](troubleshooting.md#level-3).

## Langkah 5 — Ekspor data dari SQLite

Di EC2, selagi `.env` masih mengarah ke SQLite:

```bash
cd /srv/pcm-website/app
cp db.sqlite3 db.sqlite3.bak          # backup dulu
uv run python manage.py dumpdata \
  --natural-foreign --natural-primary \
  -e contenttypes -e auth.permission -e admin.logentry -e sessions \
  --indent 2 -o data.json
```

`data.json` kini berisi semua user, halaman, berita, agenda, dan pesan kontak. Tabel yang dikecualikan akan dibuat ulang otomatis oleh `migrate`.

## Langkah 6 — Alihkan Django ke PostgreSQL lalu impor

```bash
cp .env .env.level2.bak
nano .env
```

Tambahkan (lihat [`deploy/env/level3.env.example`](../../deploy/env/level3.env.example)):

```ini
DATABASE_URL=postgres://pcm_admin:<PASSWORD>@<ENDPOINT>:5432/pcm?sslmode=require
```

Lalu:

```bash
uv run python manage.py migrate            # membuat tabel di RDS
uv run python manage.py loaddata data.json # mengimpor data Anda
sudo systemctl restart pcm
```

**Jangan** menjalankan `seed_pcm` ke RDS. Konten contoh sudah ada di dalam `data.json`.

## Langkah 7 — Verifikasi

1. `/status/` menampilkan **Level 3 terdeteksi**, `postgresql`, dan host yang berakhiran `.rds.amazonaws.com`.
2. Berita Anda, tagline Anda, dan pesan kontak dari Level 1 masih ada.
3. Anda bisa login ke admin dengan username dan password yang **sama**.
4. Buat data baru (berita atau pesan kontak). Data harus tersimpan tanpa error.
5. Dari **laptop** Anda (bukan EC2), tunjukkan bahwa database tidak bisa diakses dari internet:
   ```bash
   nslookup <ENDPOINT>            # menghasilkan alamat privat 10.0.x.x
   nc -vz -w 5 <ENDPOINT> 5432    # timeout (Windows: Test-NetConnection <ENDPOINT> -Port 5432)
   ```

## Bukti (untuk laporan)

- [ ] Tab *Connectivity & security* instance RDS: endpoint, VPC, subnet group, **Publicly accessible: No**, security group
- [ ] DB subnet group yang menunjukkan dua subnet privat di dua AZ
- [ ] Inbound rules `pcm-<kelompok>-db-sg` (source = `web-sg`)
- [ ] Sesi `psql` dari EC2 (tanpa password terlihat), mis. menjalankan `\dt`
- [ ] Halaman `/status/` yang menunjukkan Level 3
- [ ] Daftar *Pesan masuk* di admin yang memuat pesan dari Level 1
- [ ] Terminal laptop yang menunjukkan IP privat dan koneksi yang gagal

## Pertanyaan

1. Mengapa RDS diletakkan di subnet privat dengan *Public access: No*? Bagaimana EC2 bisa mengaksesnya, dan mengapa laptop Anda tidak bisa?
2. Mengapa rule `db-sg` memakai `web-sg` sebagai source, bukan IP privat EC2?
3. Sebutkan dua hal yang dikerjakan RDS untuk Anda, yang harus Anda kerjakan sendiri jika menginstal PostgreSQL di EC2.
4. Setelah level ini, apakah instance EC2 sudah "stateless"? Apa saja yang dibutuhkan untuk menjalankan website di instance yang benar-benar baru?

🎉 Selesai. Lihat [rubrik](rubric.md) untuk tugas bonus, dan jangan lupa [membersihkan resource](troubleshooting.md#cleanup) setelah penilaian.
