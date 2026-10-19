# Grading rubric

> 🇮🇩 Versi Bahasa Indonesia: [../id/rubric.md](../id/rubric.md)

Levels are graded in order. A level only counts when the previous one fully works. The final score is capped at **100**.

## Level 1 — VPC + EC2 (max 60)

| Criterion | Points | Full marks when |
|---|---|---|
| VPC design | 15 | Custom VPC `10.0.0.0/16` with DNS hostnames on; 2 public + 2 private subnets in 2 AZs; IGW attached; public route table with `0.0.0.0/0 → IGW` on public subnets only; private route table with `local` only |
| Security group | 10 | Only 80 from anywhere and 22 only from members' IPs (each `/32`); no other open ports |
| Server setup | 15 | Elastic IP; Gunicorn runs under systemd and survives reboot; Nginx proxies to `127.0.0.1:8000` and serves `/static/` and `/media/` |
| Working app | 10 | Site styled, admin login works, image upload visible, contact form works, `DEBUG=false`, `/status/` shows Level 1, tagline shows the group name |
| Report & questions | 10 | Correct architecture diagram, complete evidence, answers show understanding |

## Level 2 — S3 (+20, max 80)

| Criterion | Points | Full marks when |
|---|---|---|
| Bucket & policy | 5 | ACLs disabled; bucket policy grants `s3:GetObject` only on `static/*` and `media/*`; listing denied |
| IAM role | 5 | Role attached to the instance with a policy scoped to the bucket; **no access keys anywhere** |
| Working on S3 | 7 | `collectstatic` to S3; Level 1 media synced; new uploads land in S3; page source shows S3 URLs; `/status/` shows Level 2 |
| Report & questions | 3 | Updated diagram, evidence, answers |

## Level 3 — RDS (+20, max 100)

| Criterion | Points | Full marks when |
|---|---|---|
| RDS placement | 6 | PostgreSQL in a DB subnet group of the 2 private subnets; *Publicly accessible: No* |
| Security group chaining | 4 | `db-sg` allows 5432 **only** from `web-sg` |
| Data migration | 6 | Level 1 data (contact message, news, admin user) present in RDS; connection uses `sslmode=require`; `/status/` shows Level 3 |
| Report & questions | 4 | Updated diagram, laptop test proving RDS is private, answers |

## Bonus (up to +10, final score still capped at 100)

| Task | Points |
|---|---|
| HTTPS with your own (sub)domain and Let's Encrypt (`certbot --nginx`), plus `SECURE_COOKIES=true` | +4 |
| CloudFront in front of the S3 bucket (`AWS_S3_CUSTOM_DOMAIN`), with the bucket no longer public (Origin Access Control) | +4 |
| Port 22 closed; administer the server with SSM Session Manager or EC2 Instance Connect Endpoint | +3 |
| S3 Gateway VPC Endpoint, with evidence that S3 traffic uses it | +2 |
| Entire infrastructure written as code (CloudFormation or Terraform), included in the report | +4 |
| CloudWatch alarm (EC2 CPU or RDS free storage) with email notification | +2 |

## Deductions

| Issue | Points |
|---|---|
| AWS access keys found on the server, in `.env`, or visible in the report or video | −10 |
| SSH (22) or PostgreSQL (5432) open to `0.0.0.0/0` | −5 each |
| Resource names do not include the group name | −5 |
| Group members share the root account login instead of using their own IAM users | −5 |
| Passwords or `SECRET_KEY` visible in the report or video | −5 |
| Late submission | per course policy |
| Same instance ID, bucket, IP or report content as another group | score 0 for both groups |
| Member with no recorded contribution | that member's score reduced, per lecturer's judgement |
