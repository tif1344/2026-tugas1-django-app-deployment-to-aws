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

## Tes · Tests

```bash
cd app
uv run python manage.py test
```
