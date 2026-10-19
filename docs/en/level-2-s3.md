# Level 2 — EC2 + S3 for static and media files

> 🇮🇩 Versi Bahasa Indonesia: [../id/level-2-s3.md](../id/level-2-s3.md)

**Prerequisite:** Level 1 is working.

**Goal:** CSS, JavaScript, images and uploaded documents are stored in and served from an S3 bucket instead of the EC2 disk. The instance gets permission to write to the bucket through an **IAM role**. There are no access keys anywhere.

```
   Browser ──HTML──▶ EC2 (Nginx + Gunicorn + SQLite)
      │                     │  upload / collectstatic
      │                     │  (credentials from IAM role)
      │                     ▼
      └──images, CSS──▶ S3 bucket pcm-<group>-assets
                          ├── static/   (collectstatic)
                          └── media/    (admin uploads)
```

Django still renders the pages, but every `src="..."` and `href="..."` for files now points to `https://pcm-<group>-assets.s3.<region>.amazonaws.com/...`. The browser downloads those files directly from S3.

---

## Step 1 — Create the bucket

**S3 → Create bucket** (same region as your EC2):

- Bucket name: `pcm-<group>-assets`. Bucket names are global; add a suffix if the name is taken.
- Object Ownership: **ACLs disabled (Bucket owner enforced)**
- Block Public Access: **uncheck "Block all public access"** and tick the acknowledgement. We only allow public *reading* of two folders, through the bucket policy in the next step.
- Versioning: disabled. Default encryption: SSE-S3 (default).

## Step 2 — Bucket policy (public read for `static/` and `media/` only)

Bucket → *Permissions → Bucket policy* → paste [`deploy/aws/s3-bucket-policy.json`](../../deploy/aws/s3-bucket-policy.json) and replace `BUCKET_NAME` with your bucket name.

This lets anyone **read** objects under `static/` and `media/`. Nobody can list the bucket, and nobody can write to it except the EC2 role.

## Step 3 — IAM role for the EC2 instance

1. **IAM → Roles → Create role** → Trusted entity: *AWS service* → Use case: **EC2** → Next.
2. Skip the managed policies → name it `pcm-<group>-ec2-s3-role` → Create.
3. Open the role → *Add permissions → Create inline policy* → JSON → paste [`deploy/aws/ec2-s3-role-policy.json`](../../deploy/aws/ec2-s3-role-policy.json), replace `BUCKET_NAME`, and name it `pcm-s3-access`.
4. **EC2 → your instance → Actions → Security → Modify IAM role** → choose `pcm-<group>-ec2-s3-role`.

In your report, explain what each statement in the policy allows, and why the role gets nothing more than that (least privilege).

## Step 4 — Check the role from the instance

```bash
sudo snap install aws-cli --classic
aws sts get-caller-identity        # "Arn" should contain assumed-role/<your role name>
aws s3 ls s3://pcm-<group>-assets    # no error (empty output is fine)
```

There is no `aws configure` and there are no keys. The CLI, like boto3 inside Django, gets temporary credentials from the instance metadata service.

## Step 5 — Move existing media files

The images created in Level 1 are still in `/srv/pcm-website/app/media/`. Copy them to the bucket with the same folder layout:

```bash
cd /srv/pcm-website/app
aws s3 sync media/ s3://pcm-<group>-assets/media/
```

## Step 6 — Switch Django to S3

```bash
cd /srv/pcm-website/app
cp .env .env.level1.bak
nano .env
```

Keep your `SECRET_KEY`, `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`. Change or add these lines (see [`deploy/env/level2.env.example`](../../deploy/env/level2.env.example)):

```ini
USE_S3=true
AWS_STORAGE_BUCKET_NAME=pcm-<group>-assets
AWS_S3_REGION_NAME=<your region, e.g. us-east-1>
```

Upload the static files to S3, then restart:

```bash
uv run python manage.py collectstatic --noinput     # uploads ~130 files to s3://.../static/
sudo systemctl restart pcm
```

No Python file was edited. [`app/pcm/settings.py`](../../app/pcm/settings.py) reads `USE_S3` and switches storage backends. Read the `USE_S3` block and be ready to explain it.

## Step 7 — Verify

1. `http://<EIP>/status/` shows **Level 2 terdeteksi**, `S3Storage`, your bucket name, and S3 URLs for `STATIC_URL` and `MEDIA_URL`.
2. On the home page, right-click → *View page source*. The stylesheet and images now load from `...s3....amazonaws.com`.
3. In the admin, upload a new image (e.g. a new *Berita*). It appears on the site, and in the S3 console under `media/posts/<year>/<month>/`. Check that no new file appeared in `/srv/pcm-website/app/media/`.
4. The admin pages are still styled, because their CSS also comes from S3.
5. Open an S3 URL such as `https://pcm-<group>-assets.s3.<region>.amazonaws.com/` (the bucket root) in a browser. It should return **AccessDenied**, because listing is not allowed. Individual files under `static/` and `media/` should open.

## Evidence (for the report)

- [ ] Bucket *Permissions* tab: Block Public Access settings and the bucket policy
- [ ] Bucket *Objects* view showing the `static/` and `media/` folders
- [ ] IAM role with its trust relationship and inline policy
- [ ] EC2 instance details showing the attached IAM role
- [ ] Output of `aws sts get-caller-identity` on the instance
- [ ] Page source showing S3 URLs, and the `/status/` page
- [ ] The S3 object you uploaded through the admin

## Questions

1. Why is an IAM role safer than putting `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `.env`?
2. The bucket policy allows `s3:GetObject` only on `static/*` and `media/*`. What would change if it allowed `arn:aws:s3:::pcm-<group>-assets/*` instead? What about `s3:*`?
3. Name two benefits of serving files from S3 instead of the EC2 disk, thinking about running **two or more** EC2 instances behind a load balancer.
4. Which part of the application still lives only on the EC2 disk after Level 2?

➡️ Next: [Level 3 — RDS](level-3-rds.md)
