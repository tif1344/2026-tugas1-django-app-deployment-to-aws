# Level 1 — VPC + EC2

> 🇮🇩 Versi Bahasa Indonesia: [../id/level-1-ec2-vpc.md](../id/level-1-ec2-vpc.md)

**Goal:** the PCM website runs on one EC2 instance inside a VPC you built yourself. Nginx receives requests and serves static and media files from disk. Gunicorn runs Django. The database is a SQLite file on the same disk.

```
                Internet
                    │  HTTP :80   SSH :22 (group members' IPs only)
          ┌─────────▼──────────── VPC 10.0.0.0/16 ───────────────────────────┐
          │   Internet Gateway                                               │
          │         │                                                        │
          │  ┌──────▼─── public-a 10.0.1.0/24 ──┐  ┌─ public-b 10.0.2.0/24 ┐ │
          │  │ EC2 web server (Elastic IP)      │  │ (empty for now)       │ │
          │  │  Nginx :80 ──▶ Gunicorn :8000    │  └───────────────────────┘ │
          │  │  Django + SQLite + media/        │                            │
          │  └──────────────────────────────────┘                            │
          │  ┌─ private-a 10.0.11.0/24 ─┐  ┌─ private-b 10.0.12.0/24 ─┐      │
          │  │ (used in Level 3)        │  │ (used in Level 3)        │      │
          │  └──────────────────────────┘  └──────────────────────────┘      │
          └──────────────────────────────────────────────────────────────────┘
```

Why create private subnets now if they stay empty until Level 3? An RDS database needs a *DB subnet group* with subnets in **at least two Availability Zones**. Planning the network up front is part of designing it properly.

---

## Step 1 — Build the VPC

Do this by hand in the **VPC console**, one component at a time, so you understand every piece. (If you use the "VPC and more" wizard instead, set **NAT gateways = None** and explain every resource it created in your report.)

1. **Create VPC** → *VPC only*
   - Name: `pcm-<group>-vpc`, IPv4 CIDR: `10.0.0.0/16`
   - After creating it: *Actions → Edit VPC settings* → enable **DNS resolution** and **DNS hostnames**. RDS needs these in Level 3.
2. **Create 4 subnets** in `pcm-<group>-vpc`:

   | Name | AZ | CIDR |
   |---|---|---|
   | `pcm-<group>-public-a` | first AZ (e.g. `ap-southeast-3a`) | `10.0.1.0/24` |
   | `pcm-<group>-public-b` | second AZ (e.g. `ap-southeast-3b`) | `10.0.2.0/24` |
   | `pcm-<group>-private-a` | first AZ | `10.0.11.0/24` |
   | `pcm-<group>-private-b` | second AZ | `10.0.12.0/24` |

3. **Internet Gateway** → create `pcm-<group>-igw` → *Actions → Attach to VPC* → `pcm-<group>-vpc`.
4. **Route tables**
   - Create `pcm-<group>-public-rt`. Add the route `0.0.0.0/0 → pcm-<group>-igw`. Under *Subnet associations*, associate `public-a` and `public-b`.
   - Create `pcm-<group>-private-rt`. Keep only the default `local` route. Associate `private-a` and `private-b`.

   A subnet is "public" **only** because its route table sends `0.0.0.0/0` to an Internet Gateway. Nothing else makes it public.

## Step 2 — Security group

Create `pcm-<group>-web-sg` in `pcm-<group>-vpc`:

| Type | Port | Source | Why |
|---|---|---|---|
| HTTP | 80 | `0.0.0.0/0` | public website |
| SSH | 22 | **My IP** (one rule per member, each a `/32`) | only your group can log in |

Do not open port 8000 or anything else. Gunicorn listens on `127.0.0.1` only and is reached through Nginx.

> Campus Wi-Fi or mobile data can change your public IP. If SSH suddenly times out, update the SSH rule to your new IP.

## Step 3 — Launch the EC2 instance

**EC2 → Launch instance**

- Name: `pcm-<group>-web`
- AMI: **Ubuntu Server 24.04 LTS** (64-bit x86)
- Instance type: `t3.micro`
- Key pair: create `pcm-<group>-key` (.pem) and keep the file safe. Share it only with your group members.
- Network settings → *Edit*:
  - VPC `pcm-<group>-vpc`, subnet `pcm-<group>-public-a`, **Auto-assign public IP: Enable**
  - Select existing security group `pcm-<group>-web-sg`
- Storage: 20 GiB gp3

Then give it a fixed address: **EC2 → Elastic IPs → Allocate**, name it `pcm-<group>-eip`, then *Actions → Associate* it with `pcm-<group>-web`. Without an Elastic IP, the public IP changes every time the instance stops. That breaks `ALLOWED_HOSTS` and your submitted URL.

Connect (replace `<EIP>` with your Elastic IP):

```bash
chmod 400 pcm-<group>-key.pem
ssh -i pcm-<group>-key.pem ubuntu@<EIP>
```

## Step 4 — Install the software

On the instance:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx git

# uv: Python package and environment manager
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env
uv --version
```

## Step 5 — Get the code and configure it

The app lives in `/srv/pcm-website`, not your home folder, because Nginx (user `www-data`) cannot read files inside `/home/ubuntu`.

```bash
sudo mkdir -p /srv/pcm-website
sudo chown ubuntu:ubuntu /srv/pcm-website
git clone https://github.com/tif1344/2026-tugas1-django-app-deployment-to-aws.git /srv/pcm-website
cd /srv/pcm-website/app

uv sync --frozen                      # creates .venv and installs dependencies
cp ../deploy/env/level1.env.example .env
uv run python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
nano .env                             # paste the SECRET_KEY, put your Elastic IP in ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS
```

Prepare the database, the static files and the sample content:

```bash
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
uv run python manage.py seed_pcm          # fictional sample content + images in media/
uv run python manage.py createsuperuser
```

## Step 6 — Run Gunicorn as a service

```bash
sudo cp /srv/pcm-website/deploy/systemd/pcm.service /etc/systemd/system/pcm.service
sudo systemctl daemon-reload
sudo systemctl enable --now pcm
sudo systemctl status pcm               # should say "active (running)"
curl -I http://127.0.0.1:8000/          # expect HTTP/1.1 200 OK
```

Read [`deploy/systemd/pcm.service`](../../deploy/systemd/pcm.service). systemd restarts Gunicorn if it crashes and starts it again when the server boots.

## Step 7 — Put Nginx in front

```bash
sudo cp /srv/pcm-website/deploy/nginx/pcm.conf /etc/nginx/sites-available/pcm
sudo ln -s /etc/nginx/sites-available/pcm /etc/nginx/sites-enabled/pcm
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Read [`deploy/nginx/pcm.conf`](../../deploy/nginx/pcm.conf). `/static/` and `/media/` are served from disk by Nginx; everything else is proxied to Gunicorn.

## Step 8 — Verify

1. Open `http://<EIP>/`. The site loads with its green styling. If the CSS is missing, static files are not being served.
2. Open `http://<EIP>/status/`. It must show **Level 1 terdeteksi**, your EC2 instance ID, `sqlite` and `FileSystemStorage`.
3. Log in at `http://<EIP>/admin/`:
   - Change the tagline in *Profil organisasi* to `Deployed by <group>`.
   - Create a news item (*Berita*) with your own image. It should appear on the home page.
4. Send a message through the contact form (*Kontak*). It should appear in the admin under *Pesan masuk*. You will use this message in Level 3 to prove that data survived the migration.
5. Reboot (`sudo reboot`), wait a minute, and check the site comes back by itself.

## Evidence (for the report)

- [ ] VPC resource map (*VPC → your VPC → Resource map*) showing the subnets, route tables and IGW
- [ ] Route tables `public-rt` and `private-rt`: routes and subnet associations
- [ ] Inbound rules of `pcm-<group>-web-sg`
- [ ] EC2 instance details: subnet, Elastic IP, security group
- [ ] `sudo systemctl status pcm` and `sudo systemctl status nginx` in the terminal
- [ ] Home page with your tagline in the header, plus the news item you created
- [ ] `/status/` page

## Questions (answer briefly in the report)

1. What makes `public-a` a public subnet and `private-a` a private one?
2. Why does the web security group allow SSH only from your members' IPs? What could happen if it allowed `0.0.0.0/0`?
3. What does Nginx do that Gunicorn alone does not? Why does Gunicorn listen on `127.0.0.1` instead of `0.0.0.0`?
4. In this setup, what happens to uploaded images and the database if the EC2 instance is terminated? (This is the reason for Levels 2 and 3.)

➡️ Next: [Level 2 — S3](level-2-s3.md)
