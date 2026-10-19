# Troubleshooting & cleanup

> 🇮🇩 Versi Bahasa Indonesia: [../id/troubleshooting.md](../id/troubleshooting.md)

Before anything else, check the logs:

```bash
sudo systemctl status pcm            # is Gunicorn running?
journalctl -u pcm -n 50 --no-pager   # Django/Gunicorn errors
sudo tail -n 50 /var/log/nginx/error.log
```

After **any** change to `.env`, run `sudo systemctl restart pcm`.

## General / Level 1

| Symptom | Likely cause | Fix |
|---|---|---|
| SSH: `Connection timed out` | SG rule for 22 has an old IP; no route to IGW; no public IP | Update the SSH rule to *My IP*; check `public-rt` has `0.0.0.0/0 → igw` and is associated with the subnet; check the Elastic IP is associated |
| SSH: `Permission denied (publickey)` | Wrong key or user | User is `ubuntu`; `chmod 400` the `.pem`; use the key chosen at launch |
| Browser cannot reach the site at all | SG has no port 80; Nginx not running; you typed `https://` | Add HTTP 80; `sudo systemctl status nginx`; use `http://` |
| Nginx welcome page instead of the site | Default site still enabled | `sudo rm /etc/nginx/sites-enabled/default && sudo systemctl reload nginx` |
| **502 Bad Gateway** | Gunicorn is not running | `journalctl -u pcm -n 50`; common causes: wrong path in `pcm.service`, `uv sync` not run, a syntax error in `.env` |
| **400 Bad Request** | Host not in `ALLOWED_HOSTS` | Put the exact IP or domain you type in the browser into `ALLOWED_HOSTS`, then restart |
| `ImproperlyConfigured: SECRET_KEY must be set` | `.env` missing or `SECRET_KEY` empty | `.env` must be in `/srv/pcm-website/app/` |
| **403 CSRF verification failed** on admin login | Accessing via a host not in `CSRF_TRUSTED_ORIGINS` | Add `http://<EIP>` (with scheme) to `CSRF_TRUSTED_ORIGINS` |
| Site loads without CSS (Level 1) | `collectstatic` not run, or Nginx path wrong | Run `collectstatic`; check `alias` paths in `pcm.conf` end with `/` |
| Uploaded images 404 (Level 1) | Nginx cannot read `/srv/...`, or the media path is wrong | Check `ls -l /srv/pcm-website/app/media`; the app must be in `/srv`, not `/home/ubuntu` |
| **413 Request Entity Too Large** | Upload bigger than Nginx allows | `client_max_body_size` in `pcm.conf` (10M by default) |
| `uv: command not found` | Shell not reloaded after installing uv | `source ~/.local/bin/env` or log out and back in |
| Jakarta missing from the region list, or `OptInRequired` / "not enabled" errors | The Jakarta region has not been enabled for the account | Account owner: *Account → AWS Regions → Asia Pacific (Jakarta) → Enable*, wait a few minutes, then pick **Jakarta** in the region selector |
| Resources "disappeared" from the console | Region selector switched away from Jakarta | Pick **Asia Pacific (Jakarta)** in the region selector at the top right |

## Level 2

| Symptom | Likely cause | Fix |
|---|---|---|
| `ImproperlyConfigured: USE_S3=true requires ...` | Bucket name or region missing in `.env` | Set `AWS_STORAGE_BUCKET_NAME` and `AWS_S3_REGION_NAME` |
| `NoCredentialsError` / `Unable to locate credentials` | No IAM role attached | Attach the role, wait ~30 s, retry |
| `AccessDenied` during `collectstatic` or upload | Role policy has the wrong bucket name, or is missing actions | Compare the policy ARNs with your bucket name; test with `aws s3 cp` |
| Images/CSS return 403 in the browser | Bucket policy missing/wrong, or Block Public Access still on | Check the policy resources end in `/static/*` and `/media/*`; check bucket-level **and** account-level Block Public Access |
| `AccessControlListNotSupported` | Code tried to set ACLs | Keep `default_acl: None` (already set) and *Bucket owner enforced* |
| Old images missing after switching | Level 1 media not copied | `aws s3 sync media/ s3://<bucket>/media/` |
| Wrong region / `PermanentRedirect` | `AWS_S3_REGION_NAME` differs from the bucket's region | Use the region shown in the bucket's properties |

## Level 3

| Symptom | Likely cause | Fix |
|---|---|---|
| `migrate` or `psql` hangs, then times out | `db-sg` doesn't allow 5432 from `web-sg`; RDS in the wrong VPC | Fix the inbound rule; check the RDS VPC and subnet group |
| `could not translate host name` | Typo in the endpoint; VPC DNS settings off | Copy the endpoint again; enable DNS resolution and hostnames on the VPC |
| `password authentication failed` | Wrong password, or special characters in `DATABASE_URL` | Use letters and digits only, or URL-encode (`@` → `%40`, `#` → `%23`, `/` → `%2F`) |
| `database "pcm" does not exist` | Initial database name left empty | `psql "host=<ENDPOINT> dbname=postgres user=pcm_admin sslmode=require"` → `CREATE DATABASE pcm;` |
| `loaddata` fails with `IntegrityError` / duplicate key | `loaddata` run twice, or `seed_pcm` was run on RDS | `uv run python manage.py flush --noinput`, then `loaddata data.json` again |
| `/status/` says *Konfigurasi di luar level tugas* | Postgres connected but `USE_S3` is off, or the host is not RDS | Check `.env` contains both the Level 2 and Level 3 settings |
| Admin login fails after migration | `auth` excluded from the dump | Re-run `dumpdata` exactly as shown (only `auth.permission` is excluded) |

---

## Cleanup

Do this **only after your grade is published**. Delete in this order; some resources block deleting others.

1. **RDS:** delete `pcm-<group>-db` (untick *Create final snapshot*, tick the acknowledgement). Then delete the DB subnet group.
2. **S3:** *Empty* the bucket, then *Delete* it.
3. **EC2:** terminate `pcm-<group>-web`.
4. **Elastic IP:** *Release* it. An unattached Elastic IP is still billed.
5. **IAM:** delete `pcm-<group>-ec2-s3-role`, and the IAM users created for group members.
6. **Security groups:** delete `db-sg`, then `web-sg`.
7. **VPC:** delete `pcm-<group>-vpc`. This also removes its subnets, route tables and IGW.
8. Check **Billing → Bills** and **EC2 → Volumes / Snapshots** for anything left over.
