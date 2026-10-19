# Tugas 1 — Deploy Website Django ke AWS

**Mata kuliah:** Cloud Computing (TIF1344X) · **Semester:** tahun ke-2 · **Jenis:** kelompok

> 🇬🇧 English version: [../en/assignment.md](../en/assignment.md)

## Skenario

Sebuah Pimpinan Cabang Muhammadiyah (PCM) ingin websitenya bisa diakses secara online. Websitenya sudah dibuat dengan Django. Isinya: halaman profil, struktur pimpinan, daftar ranting, amal usaha, berita, agenda, unduhan, formulir kontak, dan panel admin untuk pengurus.

Tugas Anda adalah men-deploy website tersebut ke AWS. Anda mulai dengan satu server, lalu memindahkan bagian-bagiannya ke layanan terkelola (*managed service*) AWS.

Kode awal ada di folder [`app/`](../../app). Anda **tidak** perlu menulis kode Django. Semua level memakai kode yang sama; yang Anda ubah hanya konfigurasi server dan file `.env`.

## Capaian pembelajaran

Setelah menyelesaikan tugas ini, Anda mampu:

1. Merancang VPC dengan subnet publik dan privat di dua Availability Zone.
2. Memakai security group untuk hanya mengizinkan lalu lintas yang dibutuhkan tiap komponen.
3. Menjalankan aplikasi web Python di EC2 untuk produksi dengan Gunicorn, Nginx, dan systemd.
4. Menyimpan file statis dan file unggahan di S3, dengan IAM role (bukan access key).
5. Memindahkan database dari SQLite ke PostgreSQL terkelola di RDS tanpa kehilangan data.
6. Menjelaskan mengapa setiap perubahan tersebut membuat sistem lebih andal atau lebih mudah diskalakan.

## Tiga level

Setiap level dibangun di atas level sebelumnya. Anda memakai VPC, instance EC2, dan data yang sama dari awal sampai akhir. Kerjakan secara berurutan.

| Level | Layanan | Yang Anda bangun | Nilai maks |
|---|---|---|---|
| [1](level-1-ec2-vpc.md) | VPC, EC2 | VPC sendiri, EC2 dengan Nginx + Gunicorn, SQLite dan file di disk server | 60 |
| [2](level-2-s3.md) | + S3, IAM | File statis dan media dipindah ke S3, akses lewat IAM role | 80 |
| [3](level-3-rds.md) | + RDS | Database dipindah ke PostgreSQL di RDS dalam subnet privat, data lama ikut dimigrasi | 100 |

Anda boleh berhenti di level mana pun. Nilai Anda dibatasi oleh nilai maksimum level tersebut. Lihat [rubrik](rubric.md) untuk rincian dan tugas bonus.

```
Level 1                     Level 2                       Level 3
┌──────── VPC ────────┐     ┌──────── VPC ────────┐       ┌──────── VPC ─────────────────┐
│ subnet publik       │     │ subnet publik       │       │ subnet publik  subnet privat │
│ ┌─────────────────┐ │     │ ┌─────────────────┐ │       │ ┌───────────┐  ┌───────────┐ │
│ │ EC2             │ │     │ │ EC2             │ │       │ │ EC2       │─▶│ RDS       │ │
│ │ Nginx+Gunicorn  │ │     │ │ Nginx+Gunicorn  │ │       │ │           │  │ PostgreSQL│ │
│ │ SQLite + file   │ │     │ │ SQLite          │ │       │ └─────┬─────┘  └───────────┘ │
│ └─────────────────┘ │     │ └───────┬─────────┘ │       └───────┼──────────────────────┘
└─────────────────────┘     └─────────┼───────────┘               ▼
                                      ▼ IAM role                 S3 (statis + media)
                                  S3 (statis + media)
```

## Akun AWS

Setiap kelompok memakai **satu akun AWS** (Free Tier / *free plan*) milik salah satu anggota.

- Pemilik akun mengaktifkan **MFA untuk root user**, lalu tidak lagi memakai root untuk pekerjaan sehari-hari.
- Pemilik akun membuat **IAM user dengan akses konsol untuk setiap anggota**, termasuk dirinya sendiri. Anggota tidak boleh berbagi login root.
- Pilih satu region (mis. `ap-southeast-1`, Singapura) dan buat semua resource di region itu. Contoh di panduan memakai `us-east-1`; ganti dengan region Anda.

> ⚠️ **Biaya.** Akun free tier pun tetap ditagih untuk beberapa hal: alamat IPv4 publik (termasuk Elastic IP, sekitar USD 0,005/jam per alamat), RDS di luar kuota gratis, dan resource yang lupa dihapus. Pasang **AWS Budget** alert (mis. USD 5) sebelum mulai. Jangan pernah membuat NAT Gateway untuk tugas ini: tidak diperlukan dan biayanya sekitar USD 32/bulan. Hapus semua resource setelah penilaian ([cleanup](troubleshooting.md#cleanup)).

## Aturan penamaan (wajib)

Setiap nama resource harus memuat **nama kelompok**, agar pekerjaan Anda bisa dibedakan dari kelompok lain. Tulis nama kelompok hanya dengan huruf kecil, angka, dan tanda hubung, tanpa spasi, karena nama bucket S3 tidak mengizinkan karakter lain (mis. `kelompok-03`). Di mana pun panduan menulis `<kelompok>`, pakai nama ini.

| Resource | Nama |
|---|---|
| VPC | `pcm-<kelompok>-vpc` |
| Subnet | `pcm-<kelompok>-public-a`, `pcm-<kelompok>-public-b`, `pcm-<kelompok>-private-a`, `pcm-<kelompok>-private-b` |
| Instance EC2 | `pcm-<kelompok>-web` |
| Bucket S3 | `pcm-<kelompok>-assets` |
| Instance RDS | `pcm-<kelompok>-db` |

Selain itu, setelah deploy, login ke admin Django dan ubah **tagline** di *Profil organisasi* menjadi `Deployed by <kelompok>`. Tagline ini tampil di header website.

## Yang dikumpulkan

Kumpulkan melalui [LMS — diisi dosen] sebelum **[tenggat — diisi dosen]**:

1. **Laporan (PDF)**, berisi:
   - di sampul: nama kelompok, serta nama dan NIM setiap anggota,
   - tabel kontribusi: apa yang dikerjakan setiap anggota,

   dan untuk setiap level yang Anda selesaikan:
   - diagram arsitektur yang Anda bangun (draw.io atau sejenisnya; foto gambar tangan tidak diterima),
   - screenshot yang tercantum di bagian **Bukti** pada level tersebut,
   - jawaban singkat untuk bagian **Pertanyaan** pada level tersebut (dengan kata-kata sendiri).
2. **Video demo** (5–10 menit, link YouTube *unlisted* atau Google Drive). **Setiap anggota** mempresentasikan sebagian. Video menunjukkan:
   - website yang sudah online beserta halaman `/status/`,
   - konsol AWS untuk setiap resource,
   - satu kali unggah gambar lewat admin dan di mana file itu tersimpan.
3. **URL publik** website Anda: `http://<Elastic IP>/`. Biarkan tetap menyala sampai **[tanggal penilaian — diisi dosen]**.

Jangan pernah menampilkan password, secret key, atau AWS access key di laporan maupun video. Samarkan (*blur*) jika terlanjur muncul di layar.

## Aturan

- Tugas kelompok. Setiap anggota wajib terlibat dan mampu menjelaskan langkah mana pun, bukan hanya langkah yang ia kerjakan sendiri.
- Berdiskusi tentang masalah dengan kelompok lain boleh; berbagi screenshot, laporan, atau akun AWS tidak boleh. Laporan dua kelompok yang memuat instance ID, bucket, atau IP yang sama sama-sama diberi nilai 0.
- Jangan menaruh AWS access key di server atau di file apa pun. Rubrik memberi pengurangan nilai untuk hal ini.
- Anda boleh memakai asisten AI untuk memahami error, tetapi Anda harus bisa menjelaskan setiap langkah saat demo atau tanya jawab.

## Mulai dari mana

1. Baca halaman ini dan [rubrik](rubric.md).
2. Opsional: jalankan aplikasi di laptop terlebih dahulu (lihat [README](../../README.md#menjalankan-di-laptop)).
3. Ikuti [Level 1](level-1-ec2-vpc.md).
4. Jika ada yang error, lihat [Troubleshooting](troubleshooting.md).
