# Level 3 — EC2 + S3 + RDS PostgreSQL

> 🇮🇩 Versi Bahasa Indonesia: [../id/level-3-rds.md](../id/level-3-rds.md)

**Prerequisite:** Level 2 is working.

**Goal:** the database moves from the SQLite file on EC2 to **Amazon RDS for PostgreSQL** in the private subnets. The database cannot be reached from the internet, only from the web server's security group. All existing data moves across, including the contact message you sent in Level 1 and your admin account.

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
         S3 pcm-<group>-assets
```

After this level, the EC2 instance holds **no state**. Files are in S3 and data is in RDS. You could terminate the instance, launch a new one from the same code and `.env`, and the website would come back exactly as it was.

---

## Step 1 — Database security group

Create `pcm-<group>-db-sg` in `pcm-<group>-vpc`, with one inbound rule:

| Type | Port | Source |
|---|---|---|
| PostgreSQL | 5432 | **`pcm-<group>-web-sg`** (the security group, not an IP range) |

Using a security group as the source means "any instance that has `web-sg`". If the web server's IP changes, or you add a second web server, the rule still works.

## Step 2 — DB subnet group

**RDS → Subnet groups → Create**

- Name: `pcm-<group>-db-subnets`, VPC: `pcm-<group>-vpc`
- Availability Zones: both AZs you used. Subnets: **`private-a` and `private-b` only**.

## Step 3 — Create the RDS instance

**RDS → Create database**

- *Standard create* · Engine: **PostgreSQL** (latest version offered, e.g. 17.x)
- Template: **Free tier** (or *Sandbox* / *Dev/Test* if Free tier is not shown) · Deployment: **Single-AZ DB instance**
- DB instance identifier: `pcm-<group>-db`
- Master username: `pcm_admin` · Credentials management: **Self managed**. Choose a password with **letters and digits only**, so it does not need escaping in a URL.
- Instance class: `db.t3.micro` or `db.t4g.micro` · Storage: gp3, 20 GiB, **storage autoscaling off**
- Connectivity:
  - Compute resource: **Don't connect to an EC2 compute resource**. You wire it up yourself with the security groups.
  - VPC: `pcm-<group>-vpc` · DB subnet group: `pcm-<group>-db-subnets`
  - **Public access: No**
  - VPC security group: choose existing → `pcm-<group>-db-sg` (remove `default`)
- Monitoring: turn **Performance Insights** and **Enhanced Monitoring** off
- Additional configuration:
  - **Initial database name: `pcm`**. Without it, RDS does not create the database.
  - Backup retention: 1 day · Deletion protection: off (makes cleanup easier)

Creation takes about 10 minutes. When the status is *Available*, copy the **Endpoint**, e.g. `pcm-<group>-db.xxxxxxxx.us-east-1.rds.amazonaws.com`.
## Step 4 — Test the connection from EC2

```bash
sudo apt install -y postgresql-client
psql "host=<ENDPOINT> port=5432 dbname=pcm user=pcm_admin sslmode=require"
# enter the password; you should get a  pcm=>  prompt. Type \q to quit.
```

If it hangs, the problem is networking (security group or subnets), not Django. See [troubleshooting](troubleshooting.md#level-3).

## Step 5 — Export data from SQLite

On EC2, while `.env` still points at SQLite:

```bash
cd /srv/pcm-website/app
cp db.sqlite3 db.sqlite3.bak          # backup first
uv run python manage.py dumpdata \
  --natural-foreign --natural-primary \
  -e contenttypes -e auth.permission -e admin.logentry -e sessions \
  --indent 2 -o data.json
```

`data.json` now contains every user, page, news item, event and contact message. The excluded tables are rebuilt automatically by `migrate`.

## Step 6 — Switch Django to PostgreSQL and import

```bash
cp .env .env.level2.bak
nano .env
```

Add (see [`deploy/env/level3.env.example`](../../deploy/env/level3.env.example)):

```ini
DATABASE_URL=postgres://pcm_admin:<PASSWORD>@<ENDPOINT>:5432/pcm?sslmode=require
```

Then:

```bash
uv run python manage.py migrate            # creates the tables in RDS
uv run python manage.py loaddata data.json # imports your data
sudo systemctl restart pcm
```

Do **not** run `seed_pcm` against RDS. The sample content is already in `data.json`.

## Step 7 — Verify

1. `/status/` shows **Level 3 terdeteksi**, `postgresql`, and a host ending in `.rds.amazonaws.com`.
2. Your news item, your tagline, and the contact message from Level 1 are all still there.
3. You can log in to the admin with the **same** username and password.
4. Create something new (a news item or contact message). It must save without errors.
5. From your **laptop** (not EC2), show that the database is unreachable from the internet:
   ```bash
   nslookup <ENDPOINT>            # resolves to a private 10.0.x.x address
   nc -vz -w 5 <ENDPOINT> 5432    # times out (Windows: Test-NetConnection <ENDPOINT> -Port 5432)
   ```

## Evidence (for the report)

- [ ] RDS instance *Connectivity & security* tab: endpoint, VPC, subnet group, **Publicly accessible: No**, security group
- [ ] DB subnet group showing the two private subnets in two AZs
- [ ] Inbound rules of `pcm-<group>-db-sg` (source = `web-sg`)
- [ ] `psql` session from EC2 (no password visible), e.g. running `\dt`
- [ ] `/status/` page showing Level 3
- [ ] Admin *Pesan masuk* list showing the message created in Level 1
- [ ] Laptop terminal showing the private IP and the failed connection

## Questions

1. Why is RDS placed in private subnets with *Public access: No*? How does EC2 reach it, and why can't your laptop?
2. Why does the `db-sg` rule use `web-sg` as the source instead of the EC2 private IP?
3. Name two things RDS does for you that you would otherwise do yourself if you installed PostgreSQL on EC2.
4. After this level, is the EC2 instance "stateless"? What would you need to run the site on a brand-new instance?

🎉 Done. Check the [rubric](rubric.md) for bonus tasks, and remember to [clean up](troubleshooting.md#cleanup) after grading.
