# Tugas 1 · Assignment 1 — Deploy Website PCM (Django) ke AWS

Cloud Computing (TIF1344X)

| | 🇮🇩 Bahasa Indonesia | 🇬🇧 English |
|---|---|---|
| Deskripsi tugas · Assignment brief | [docs/id/assignment.md](docs/id/assignment.md) | [docs/en/assignment.md](docs/en/assignment.md) |
| Level 1 — VPC + EC2 | [docs/id/level-1-ec2-vpc.md](docs/id/level-1-ec2-vpc.md) | [docs/en/level-1-ec2-vpc.md](docs/en/level-1-ec2-vpc.md) |
| Level 2 — + S3 | [docs/id/level-2-s3.md](docs/id/level-2-s3.md) | [docs/en/level-2-s3.md](docs/en/level-2-s3.md) |
| Level 3 — + RDS | [docs/id/level-3-rds.md](docs/id/level-3-rds.md) | [docs/en/level-3-rds.md](docs/en/level-3-rds.md) |
| Rubrik · Rubric | [docs/id/rubric.md](docs/id/rubric.md) | [docs/en/rubric.md](docs/en/rubric.md) |
| Troubleshooting & cleanup | [docs/id/troubleshooting.md](docs/id/troubleshooting.md) | [docs/en/troubleshooting.md](docs/en/troubleshooting.md) |

## Isi repositori · Repository layout

```
app/               Website PCM (Django 5.2, uv)       · PCM website (Django 5.2, uv)
  pcm/settings.py  Semua konfigurasi dari .env        · All configuration comes from .env
  website/         Model, view, template, seed_pcm    · Models, views, templates, seed_pcm
deploy/
  nginx/           Konfigurasi Nginx                  · Nginx site config
  systemd/         Service Gunicorn                   · Gunicorn service
  env/             Contoh .env untuk Level 1, 2, 3    · Example .env for Levels 1, 2, 3
  aws/             Bucket policy & IAM policy (JSON)  · Bucket policy & IAM policy (JSON)
docs/id, docs/en   Panduan tugas                      · Assignment guides
```

Website contoh untuk **PCM Kartasura** (Sukoharjo, Jawa Tengah). Data pengurus, ranting, amal usaha, berita, dan agenda adalah **contoh fiktif**. · Sample website for **PCM Kartasura** (Sukoharjo, Central Java). Leaders, branch chairs, institutions, news and events are **fictional sample data**.

Logo Muhammadiyah ([`app/static/img/muhammadiyah.svg`](app/static/img/muhammadiyah.svg)): K. H. Siradj Dahlan, vektor oleh Hibensis, dari [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Muhammadiyah.svg), lisensi [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Jangan diubah; atribusi wajib tetap ada di footer website. · Muhammadiyah logo: K. H. Siradj Dahlan, vectorised by Hibensis, from Wikimedia Commons, licensed CC BY-SA 4.0. Do not modify it; the attribution in the site footer must stay.

## Menjalankan di laptop

Butuh [uv](https://docs.astral.sh/uv/getting-started/installation/). Python 3.12 diunduh otomatis oleh uv jika belum ada.

```bash
cd app
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py seed_pcm          # konten contoh + gambar
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Buka http://127.0.0.1:8000/ · admin: http://127.0.0.1:8000/admin/ · status: http://127.0.0.1:8000/status/

Hentikan server dengan `Ctrl+C`. Untuk mengembalikan konten contoh ke kondisi awal: `uv run python manage.py seed_pcm --reset`.

### Pengguna Windows

- Instal uv lewat PowerShell: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`, lalu buka terminal baru.
- Jalankan perintah di **PowerShell**; di sana `cp` tetap berfungsi. Di Command Prompt (`cmd`), pakai `copy .env.example .env`.
- Pastikan nama file tepat `.env`, bukan `.env.txt`. Notepad dan File Explorer sering menambahkan atau menyembunyikan `.txt`. Cek dengan `dir` (atau `ls`) di terminal.

### Coba admin dan unggah gambar

Sebelum ke AWS, pastikan semua bagian website berjalan di laptop:

1. Login di http://127.0.0.1:8000/admin/ dengan akun dari `createsuperuser`.
2. Buka *Profil organisasi* dan ubah tagline. Tagline baru tampil di header website.
3. Tambahkan *Berita* dengan gambar dari laptop Anda. Berita muncul di beranda, dan file gambarnya tersimpan di `app/media/posts/`.
4. Kirim pesan lewat halaman *Kontak*. Pesan muncul di admin pada menu *Pesan masuk*.
5. Buka http://127.0.0.1:8000/status/. Halaman menampilkan **Level 1 terdeteksi**, `sqlite`, dan `FileSystemStorage`.

Gambar unggahan (`media/`) dan database (`db.sqlite3`) inilah yang nanti dipindahkan ke S3 (Level 2) dan RDS (Level 3).

### Tentang file `.env`

Semua pengaturan website dibaca dari `app/.env`, bukan ditulis di kode. Di laptop, `.env.example` mengaktifkan `DEBUG=true` dan memakai SQLite serta folder `media/` lokal. Di server, Anda memakai file dari [`deploy/env/`](deploy/env/), satu per level: kodenya tetap sama, hanya `.env` yang berubah. File `.env` tidak ikut di-commit ke git (lihat `.gitignore`) karena berisi rahasia seperti `SECRET_KEY` dan password database.

## Run locally

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/). uv downloads Python 3.12 automatically if it is missing.

```bash
cd app
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py seed_pcm          # sample content + images
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Open http://127.0.0.1:8000/ · admin: http://127.0.0.1:8000/admin/ · status: http://127.0.0.1:8000/status/

Stop the server with `Ctrl+C`. To restore the sample content to its original state: `uv run python manage.py seed_pcm --reset`.

### Windows users

- Install uv from PowerShell: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`, then open a new terminal.
- Run the commands in **PowerShell**, where `cp` still works. In Command Prompt (`cmd`), use `copy .env.example .env`.
- Make sure the file is named exactly `.env`, not `.env.txt`. Notepad and File Explorer often add or hide `.txt`. Check with `dir` (or `ls`) in the terminal.

### Try the admin and an image upload

Before moving to AWS, check every part of the site works on your laptop:

1. Log in at http://127.0.0.1:8000/admin/ with the account from `createsuperuser`.
2. Open *Profil organisasi* and change the tagline. The new tagline appears in the site header.
3. Add a *Berita* (news item) with an image from your laptop. It appears on the home page, and the image file is saved in `app/media/posts/`.
4. Send a message through the *Kontak* page. It appears in the admin under *Pesan masuk*.
5. Open http://127.0.0.1:8000/status/. It shows **Level 1 terdeteksi**, `sqlite` and `FileSystemStorage`.

These uploaded images (`media/`) and this database (`db.sqlite3`) are what you will later move to S3 (Level 2) and RDS (Level 3).

### About the `.env` file

All site settings are read from `app/.env`, not written in the code. On your laptop, `.env.example` turns on `DEBUG=true` and uses SQLite and the local `media/` folder. On the server you use the files in [`deploy/env/`](deploy/env/), one per level: the code stays the same, only `.env` changes. `.env` is never committed to git (see `.gitignore`) because it holds secrets such as `SECRET_KEY` and the database password.

## Tes · Tests

```bash
cd app
uv run python manage.py test
```
