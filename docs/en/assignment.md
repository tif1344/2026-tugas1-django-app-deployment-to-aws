# Assignment 1 — Deploying a Django Website to AWS

**Course:** Cloud Computing (TIF1344X) · **Year:** 2 · **Type:** group

> 🇮🇩 Versi Bahasa Indonesia: [../id/assignment.md](../id/assignment.md)

## Scenario

A Muhammadiyah branch leadership (*Pimpinan Cabang Muhammadiyah*, PCM) wants its website online. The website is already built in Django. It has a profile page, leadership structure, branches (*ranting*), institutions (*amal usaha*), news, events, downloads, a contact form, and an admin panel for staff.

Your job is to deploy it to AWS. You start with a single server and then move parts of it to managed AWS services.

The starter code is in [`app/`](../../app). You do **not** need to write Django code. Every level uses the same code; you change only the server configuration and the `.env` file.

## Learning objectives

After this assignment you can:

1. Design a VPC with public and private subnets across two Availability Zones.
2. Use security groups to allow only the traffic each component needs.
3. Run a Python web app in production on EC2 with Gunicorn, Nginx and systemd.
4. Store static and user-uploaded files in S3, using an IAM role instead of access keys.
5. Move a database from SQLite to managed PostgreSQL on RDS without losing data.
6. Explain why each of these changes makes the system more reliable or scalable.

## The three levels

Each level builds on the previous one. You keep the same VPC, EC2 instance and data the whole way through. Do them in order.

| Level | Services | What you build | Max score |
|---|---|---|---|
| [1](level-1-ec2-vpc.md) | VPC, EC2 | Custom VPC, EC2 running Nginx + Gunicorn, SQLite and files on the server disk | 60 |
| [2](level-2-s3.md) | + S3, IAM | Static and media files moved to S3, access through an IAM role | 80 |
| [3](level-3-rds.md) | + RDS | Database moved to PostgreSQL on RDS in private subnets, existing data migrated | 100 |

You can stop after any level. Your score is capped at that level's maximum. See the [rubric](rubric.md) for details, plus bonus tasks.

```
Level 1                     Level 2                       Level 3
┌──────── VPC ────────┐     ┌──────── VPC ────────┐       ┌──────── VPC ─────────────────┐
│ public subnet       │     │ public subnet       │       │ public subnet  private subnet│
│ ┌─────────────────┐ │     │ ┌─────────────────┐ │       │ ┌───────────┐  ┌───────────┐ │
│ │ EC2             │ │     │ │ EC2             │ │       │ │ EC2       │─▶│ RDS       │ │
│ │ Nginx+Gunicorn  │ │     │ │ Nginx+Gunicorn  │ │       │ │           │  │ PostgreSQL│ │
│ │ SQLite + files  │ │     │ │ SQLite          │ │       │ └─────┬─────┘  └───────────┘ │
│ └─────────────────┘ │     │ └───────┬─────────┘ │       └───────┼──────────────────────┘
└─────────────────────┘     └─────────┼───────────┘               ▼
                                      ▼ IAM role                 S3 (static + media)
                                  S3 (static + media)
```

## AWS account

Each group uses **one AWS account** (Free Tier / free plan), owned by one member.

- The account owner turns on **MFA for the root user** and then stops using root for daily work.
- The owner creates an **IAM user with console access for each member**, including themselves. Members never share the root login.
- Pick one region (e.g. `ap-southeast-1`, Singapore) and create every resource in it. The examples in the guides use `us-east-1`; replace it with your region.

> ⚠️ **Costs.** Even free-tier accounts are charged for some things: public IPv4 addresses (including Elastic IPs, about USD 0.005/hour each), RDS beyond the free allowance, and anything you forget to delete. Set up an **AWS Budget** alert (e.g. USD 5) before you start. Never create a NAT Gateway for this assignment: it is not needed and costs about USD 32/month. Delete everything after grading ([cleanup](troubleshooting.md#cleanup)).

## Naming rule (mandatory)

Every resource name must include your **group name**, so your work can be told apart from other groups'. Write the group name in lowercase letters, digits and hyphens only, with no spaces, because S3 bucket names allow nothing else (e.g. `kelompok-03`). Wherever the guides say `<group>`, use this name.

| Resource | Name |
|---|---|
| VPC | `pcm-<group>-vpc` |
| Subnets | `pcm-<group>-public-a`, `pcm-<group>-public-b`, `pcm-<group>-private-a`, `pcm-<group>-private-b` |
| EC2 instance | `pcm-<group>-web` |
| S3 bucket | `pcm-<group>-assets` |
| RDS instance | `pcm-<group>-db` |

Also, after deploying, log in to the Django admin and change the **tagline** in *Profil organisasi* to `Deployed by <group>`. It appears in the website header.

## Deliverables

Submit through [LMS — filled in by lecturer] before **[deadline — filled in by lecturer]**:

1. **Report (PDF)** with:
   - on the cover: group name, and each member's name and NIM,
   - a contribution table: what each member did,

   and, for each level you completed:
   - an architecture diagram of what you built (draw.io or similar; hand-drawn photos are not accepted),
   - the screenshots listed in that level's **Evidence** section,
   - short answers to that level's **Questions** (in your own words).
2. **Demo video** (5–10 minutes, unlisted YouTube or Google Drive link). **Every member** presents part of it. It shows:
   - the live website and its `/status/` page,
   - the AWS console for each resource,
   - one image upload through the admin and where that file ends up.
3. **Public URL** of your site: `http://<Elastic IP>/`. Keep it running until **[grading date — filled in by lecturer]**.

Never include passwords, secret keys or AWS access keys in your report or video. Blur them if they appear on screen.

## Rules

- Group work. Every member must take part and be able to explain any step, not only the steps they did themselves.
- Discussing problems with other groups is fine; sharing screenshots, reports or AWS accounts is not. Two groups' reports showing the same instance ID, bucket or IP are both graded 0.
- Do not put AWS access keys on the server or in any file. The rubric deducts points for this.
- You may use AI assistants to understand errors, but you must be able to explain every step during the demo or Q&A.

## Where to start

1. Read this page and the [rubric](rubric.md).
2. Optional: run the app on your laptop first (see the [README](../../README.md#run-locally)).
3. Follow [Level 1](level-1-ec2-vpc.md).
4. When something breaks, check [Troubleshooting](troubleshooting.md).
