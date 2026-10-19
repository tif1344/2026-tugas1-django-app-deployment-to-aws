# Level 1 — VPC + EC2

> 🇬🇧 English version: [../en/level-1-ec2-vpc.md](../en/level-1-ec2-vpc.md)

**Tujuan:** website PCM berjalan di satu instance EC2 di dalam VPC yang Anda bangun sendiri. Nginx menerima request dan menyajikan file statis dan media dari disk. Gunicorn menjalankan Django. Database-nya berupa file SQLite di disk yang sama.

```
                Internet
                    │  HTTP :80   SSH :22 (hanya IP anggota kelompok)
          ┌─────────▼──────────── VPC 10.0.0.0/16 ───────────────────────────┐
          │   Internet Gateway                                               │
          │         │                                                        │
          │  ┌──────▼─── public-a 10.0.1.0/24 ──┐  ┌─ public-b 10.0.2.0/24 ┐ │
          │  │ EC2 web server (Elastic IP)      │  │ (masih kosong)        │ │
          │  │  Nginx :80 ──▶ Gunicorn :8000    │  └───────────────────────┘ │
          │  │  Django + SQLite + media/        │                            │
          │  └──────────────────────────────────┘                            │
          │  ┌─ private-a 10.0.11.0/24 ─┐  ┌─ private-b 10.0.12.0/24 ─┐      │
          │  │ (dipakai di Level 3)     │  │ (dipakai di Level 3)     │      │
          │  └──────────────────────────┘  └──────────────────────────┘      │
          └──────────────────────────────────────────────────────────────────┘
```

Mengapa subnet privat dibuat sekarang padahal baru dipakai di Level 3? Database RDS membutuhkan *DB subnet group* dengan subnet di **minimal dua Availability Zone**. Merencanakan jaringan sejak awal adalah bagian dari merancangnya dengan benar.

---

## Langkah 1 — Bangun VPC

Kerjakan secara manual di **konsol VPC**, satu komponen demi satu komponen, agar Anda memahami setiap bagiannya. (Jika Anda memakai wizard "VPC and more", set **NAT gateways = None** dan jelaskan setiap resource yang dibuatnya di laporan.)

1. **Create VPC** → *VPC only*
   - Nama: `pcm-<kelompok>-vpc`, IPv4 CIDR: `10.0.0.0/16`
   - Setelah dibuat: *Actions → Edit VPC settings* → aktifkan **DNS resolution** dan **DNS hostnames**. RDS membutuhkannya di Level 3.
2. **Buat 4 subnet** di `pcm-<kelompok>-vpc`:

   | Nama | AZ | CIDR |
   |---|---|---|
   | `pcm-<kelompok>-public-a` | AZ pertama (mis. `us-east-1a`) | `10.0.1.0/24` |
   | `pcm-<kelompok>-public-b` | AZ kedua (mis. `us-east-1b`) | `10.0.2.0/24` |
   | `pcm-<kelompok>-private-a` | AZ pertama | `10.0.11.0/24` |
   | `pcm-<kelompok>-private-b` | AZ kedua | `10.0.12.0/24` |

3. **Internet Gateway** → buat `pcm-<kelompok>-igw` → *Actions → Attach to VPC* → `pcm-<kelompok>-vpc`.
4. **Route table**
   - Buat `pcm-<kelompok>-public-rt`. Tambahkan route `0.0.0.0/0 → pcm-<kelompok>-igw`. Di *Subnet associations*, asosiasikan `public-a` dan `public-b`.
   - Buat `pcm-<kelompok>-private-rt`. Biarkan hanya route bawaan `local`. Asosiasikan `private-a` dan `private-b`.

   Sebuah subnet disebut "publik" **hanya** karena route table-nya mengarahkan `0.0.0.0/0` ke Internet Gateway. Tidak ada hal lain yang membuatnya publik.

## Langkah 2 — Security group

Buat `pcm-<kelompok>-web-sg` di `pcm-<kelompok>-vpc`:

| Type | Port | Source | Alasan |
|---|---|---|---|
| HTTP | 80 | `0.0.0.0/0` | website publik |
| SSH | 22 | **My IP** (satu rule per anggota, masing-masing `/32`) | hanya kelompok Anda yang bisa login |

Jangan buka port 8000 atau port lain. Gunicorn hanya mendengarkan di `127.0.0.1` dan diakses melalui Nginx.

> IP publik Anda bisa berubah jika memakai Wi-Fi kampus atau data seluler. Jika SSH tiba-tiba *timeout*, perbarui rule SSH dengan IP baru Anda.

## Langkah 3 — Jalankan instance EC2

**EC2 → Launch instance**

- Nama: `pcm-<kelompok>-web`
- AMI: **Ubuntu Server 24.04 LTS** (64-bit x86)
- Instance type: `t3.micro` (atau `t2.micro`)
- Key pair: buat `pcm-<kelompok>-key` (.pem) dan simpan file-nya baik-baik. Bagikan hanya kepada anggota kelompok Anda.
- Network settings → *Edit*:
  - VPC `pcm-<kelompok>-vpc`, subnet `pcm-<kelompok>-public-a`, **Auto-assign public IP: Enable**
  - Pilih security group yang sudah ada: `pcm-<kelompok>-web-sg`
- Storage: 20 GiB gp3

Lalu beri alamat tetap: **EC2 → Elastic IPs → Allocate**, beri nama `pcm-<kelompok>-eip`, lalu *Actions → Associate* ke `pcm-<kelompok>-web`. Tanpa Elastic IP, IP publik berubah setiap kali instance di-stop. Akibatnya `ALLOWED_HOSTS` dan URL yang Anda kumpulkan tidak berlaku lagi.

Koneksi (ganti `<EIP>` dengan Elastic IP Anda):

```bash
chmod 400 pcm-<kelompok>-key.pem
ssh -i pcm-<kelompok>-key.pem ubuntu@<EIP>
```

## Langkah 4 — Instal software

Di dalam instance:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx git

# uv: pengelola paket dan environment Python
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env
uv --version
```

## Langkah 5 — Ambil kode dan konfigurasikan

Aplikasi diletakkan di `/srv/pcm-website`, bukan di folder home, karena Nginx (user `www-data`) tidak bisa membaca file di dalam `/home/ubuntu`.

```bash
sudo mkdir -p /srv/pcm-website
sudo chown ubuntu:ubuntu /srv/pcm-website
git clone <STARTER_REPO_URL> /srv/pcm-website
cd /srv/pcm-website/app

uv sync --frozen                      # membuat .venv dan menginstal dependensi
cp ../deploy/env/level1.env.example .env
uv run python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
nano .env                             # tempel SECRET_KEY, isi Elastic IP di ALLOWED_HOSTS dan CSRF_TRUSTED_ORIGINS
```

Siapkan database, file statis, dan konten contoh:

```bash
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
uv run python manage.py seed_pcm          # konten contoh fiktif + gambar di media/
uv run python manage.py createsuperuser
```

## Langkah 6 — Jalankan Gunicorn sebagai service

```bash
sudo cp /srv/pcm-website/deploy/systemd/pcm.service /etc/systemd/system/pcm.service
sudo systemctl daemon-reload
sudo systemctl enable --now pcm
sudo systemctl status pcm               # harus "active (running)"
curl -I http://127.0.0.1:8000/          # harus HTTP/1.1 200 OK
```

Baca [`deploy/systemd/pcm.service`](../../deploy/systemd/pcm.service). systemd menyalakan ulang Gunicorn jika crash dan menjalankannya lagi saat server boot.

## Langkah 7 — Pasang Nginx di depan

```bash
sudo cp /srv/pcm-website/deploy/nginx/pcm.conf /etc/nginx/sites-available/pcm
sudo ln -s /etc/nginx/sites-available/pcm /etc/nginx/sites-enabled/pcm
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Baca [`deploy/nginx/pcm.conf`](../../deploy/nginx/pcm.conf). `/static/` dan `/media/` disajikan langsung dari disk oleh Nginx; selain itu diteruskan (*proxy*) ke Gunicorn.

## Langkah 8 — Verifikasi

1. Buka `http://<EIP>/`. Website tampil dengan warna hijaunya. Jika CSS tidak muncul, file statis belum tersaji.
2. Buka `http://<EIP>/status/`. Halaman harus menampilkan **Level 1 terdeteksi**, instance ID EC2 Anda, `sqlite`, dan `FileSystemStorage`.
3. Login di `http://<EIP>/admin/`:
   - Ubah tagline di *Profil organisasi* menjadi `Deployed by <kelompok>`.
   - Buat satu *Berita* dengan gambar milik Anda sendiri. Berita itu harus muncul di beranda.
4. Kirim pesan lewat formulir *Kontak*. Pesan harus muncul di admin pada menu *Pesan masuk*. Pesan ini dipakai di Level 3 untuk membuktikan data tidak hilang saat migrasi.
5. Reboot (`sudo reboot`), tunggu satu menit, lalu cek website kembali menyala dengan sendirinya.

## Bukti (untuk laporan)

- [ ] Resource map VPC (*VPC → VPC Anda → Resource map*) yang menunjukkan subnet, route table, dan IGW
- [ ] Route table `public-rt` dan `private-rt`: route dan subnet association-nya
- [ ] Inbound rules `pcm-<kelompok>-web-sg`
- [ ] Detail instance EC2: subnet, Elastic IP, security group
- [ ] `sudo systemctl status pcm` dan `sudo systemctl status nginx` di terminal
- [ ] Beranda dengan tagline Anda di header, beserta berita yang Anda buat
- [ ] Halaman `/status/`

## Pertanyaan (jawab singkat di laporan)

1. Apa yang membuat `public-a` menjadi subnet publik dan `private-a` subnet privat?
2. Mengapa security group web hanya mengizinkan SSH dari IP anggota kelompok? Apa yang bisa terjadi jika diizinkan dari `0.0.0.0/0`?
3. Apa yang dikerjakan Nginx yang tidak dikerjakan Gunicorn sendirian? Mengapa Gunicorn mendengarkan di `127.0.0.1`, bukan `0.0.0.0`?
4. Pada konfigurasi ini, apa yang terjadi pada gambar unggahan dan database jika instance EC2 di-*terminate*? (Inilah alasan adanya Level 2 dan 3.)

➡️ Berikutnya: [Level 2 — S3](level-2-s3.md)
