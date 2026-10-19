"""Fill the database with sample (fictional) PCM content and generated images.

Images go through Django's default storage, so they land on local disk at
Level 1 and in the S3 bucket when USE_S3=true.
"""

import io
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageColor, ImageDraw, ImageFont

from website.models import (
    Branch,
    Document,
    Event,
    Institution,
    Leader,
    Post,
    RelatedLink,
    SiteProfile,
)

PALETTE = ["#00843f", "#00703c", "#0b6e4f", "#1f7a8c", "#a6761d", "#5b8c2a"]


def placeholder_image(text, size=(1200, 675), color="#00843f", fmt="JPEG"):
    width, height = size
    background = ImageColor.getrgb(color)
    is_light = sum(background) > 600
    image = Image.new("RGB", size, background)
    draw = ImageDraw.Draw(image)
    # Diagonal bands so the image is visibly a picture, not a flat block.
    shift = -18 if is_light else 22
    band = tuple(max(0, min(255, c + shift)) for c in background)
    for i in range(-height, width, 90):
        draw.line([(i, height), (i + height, 0)], fill=band, width=3)
    font = ImageFont.load_default(size=max(24, width // 18))
    box = draw.multiline_textbbox((0, 0), text, font=font, align="center")
    x = (width - (box[2] - box[0])) / 2
    y = (height - (box[3] - box[1])) / 2
    draw.multiline_text((x, y), text, font=font, fill="#00703c" if is_light else "#ffffff", align="center")
    buffer = io.BytesIO()
    image.save(buffer, fmt, **({"quality": 85} if fmt == "JPEG" else {}))
    return ContentFile(buffer.getvalue())


PROFILE = {
    "name": "Pimpinan Cabang Muhammadiyah Kartasura",
    "short_name": "PCM Kartasura",
    "tagline": "Berkemajuan untuk umat dan bangsa",
    "about": (
        "PCM Kartasura adalah pimpinan Persyarikatan Muhammadiyah di tingkat kecamatan di "
        "Kartasura, Kabupaten Sukoharjo, Jawa Tengah, yang membina ranting-ranting dan amal "
        "usaha di wilayahnya. Kami bergerak di bidang dakwah, pendidikan, kesehatan, dan "
        "pemberdayaan masyarakat."
    ),
    "history": (
        "Sejarah lengkap PCM Kartasura dapat diisi oleh pengurus melalui halaman admin.\n\n"
        "Catatan: website ini dibuat untuk tugas kuliah Cloud Computing. Data pengurus, ranting, "
        "amal usaha, berita, dan agenda di dalamnya adalah contoh fiktif."
    ),
    "vision": "Terwujudnya masyarakat Islam yang sebenar-benarnya di wilayah cabang yang berkemajuan.",
    "mission": (
        "Menyelenggarakan dakwah amar ma'ruf nahi munkar yang mencerahkan\n"
        "Mengembangkan amal usaha di bidang pendidikan, kesehatan, dan sosial\n"
        "Memperkuat kaderisasi dan konsolidasi ranting\n"
        "Memberdayakan ekonomi jamaah"
    ),
    "address": "Kecamatan Kartasura, Kabupaten Sukoharjo, Jawa Tengah",
    "phone": "0271-000000",
    "email": "sekretariat@pcm-contoh.example",
}

LEADERS = [
    ("Ahmad Basuki", "Ketua"),
    ("Siti Rahmawati", "Wakil Ketua"),
    ("Muhammad Rizal", "Sekretaris"),
    ("Nurul Hidayah", "Bendahara"),
    ("Hasan Mahmud", "Ketua Majelis Tabligh"),
    ("Dewi Lestari", "Ketua Majelis Pendidikan Dasar dan Menengah"),
    ("Yusuf Pratama", "Ketua Majelis Pembina Kesehatan Umum"),
    ("Fatimah Azzahra", "Ketua Majelis Pemberdayaan Masyarakat"),
]

RELATED_LINKS = [
    ("PDM Sukoharjo", "https://pdmsukoharjo.or.id"),
    ("PWM Jawa Tengah", "https://pwmjateng.com"),
    ("PP Muhammadiyah", "https://muhammadiyah.or.id"),
]

# Village names are real places in Kecamatan Kartasura; the chairs are fictional.
BRANCHES = [
    ("PRM Pabelan", "Abdul Karim", "Desa Pabelan, Kartasura"),
    ("PRM Gonilan", "Rahmat Hidayat", "Desa Gonilan, Kartasura"),
    ("PRM Makamhaji", "Ilham Saputra", "Desa Makamhaji, Kartasura"),
    ("PRM Gumpang", "Bambang Setiawan", "Desa Gumpang, Kartasura"),
    ("PRM Pucangan", "Zainal Arifin", "Desa Pucangan, Kartasura"),
]

INSTITUTIONS = [
    ("SD Muhammadiyah Contoh Kartasura", "pendidikan", "Sekolah dasar dengan program tahfiz dan literasi."),
    ("SMP Muhammadiyah Contoh Kartasura", "pendidikan", "Sekolah menengah dengan kelas unggulan sains."),
    ("TK Aisyiyah Bustanul Athfal", "pendidikan", "Pendidikan anak usia dini binaan Aisyiyah."),
    ("Klinik Pratama PKU Muhammadiyah", "kesehatan", "Layanan kesehatan umum, gigi, dan ibu-anak."),
    ("Panti Asuhan Muhammadiyah", "sosial", "Pengasuhan dan pendidikan anak yatim dan dhuafa."),
    ("BMT Surya Madani", "ekonomi", "Lembaga keuangan mikro syariah untuk UMKM jamaah."),
]

POSTS = [
    ("Pengajian Ahad Pagi Bahas Fikih Muamalah Kontemporer",
     "Ratusan jamaah menghadiri pengajian bulanan yang membahas transaksi digital dalam perspektif Islam."),
    ("Musyawarah Cabang Tetapkan Program Kerja Lima Tahun",
     "Musycab menghasilkan rekomendasi penguatan ranting dan pengembangan amal usaha."),
    ("Siswa SD Muhammadiyah Raih Juara Olimpiade Sains Tingkat Kabupaten",
     "Siswa kelas lima berhasil meraih medali emas bidang matematika."),
    ("Bakti Sosial dan Pemeriksaan Kesehatan Gratis",
     "Klinik PKU bersama Aisyiyah melayani lebih dari 200 warga dalam kegiatan bakti sosial."),
    ("Pelatihan Kader Tingkat Cabang Diikuti 60 Peserta",
     "Baitul Arqam cabang membekali kader muda dengan ideologi dan manajemen organisasi."),
    ("Penyaluran Zakat Fitrah dan Qurban oleh Lazismu Cabang",
     "Lazismu menyalurkan bantuan kepada keluarga prasejahtera di lima ranting."),
    ("Peresmian Gedung Baru TK Aisyiyah",
     "Gedung dua lantai siap menampung lebih banyak peserta didik mulai tahun ajaran baru."),
]

EVENTS = [
    ("Pengajian Ahad Pagi", 6, "Masjid At-Taqwa", "Kajian rutin bulanan terbuka untuk umum."),
    ("Rapat Pleno Pimpinan Cabang", 12, "Gedung Dakwah PCM", "Evaluasi program triwulan."),
    ("Kajian Ramadan Keluarga Sakinah", 20, "Aula SMP Muhammadiyah Contoh Kartasura", "Bersama Majelis Tarjih."),
    ("Jalan Sehat Milad Muhammadiyah", 34, "Lapangan Kecamatan", "Doorprize dan pemeriksaan kesehatan gratis."),
    ("Silaturahmi Ranting", -10, "PRM Pabelan", "Kunjungan pimpinan cabang ke ranting."),
]

BODY = (
    "{lead}\n\n"
    "Kegiatan ini merupakan bagian dari program kerja Pimpinan Cabang Muhammadiyah Kartasura "
    "untuk memperkuat dakwah dan pelayanan kepada masyarakat. Ketua PCM menyampaikan apresiasi "
    "kepada seluruh panitia, ranting, dan amal usaha yang terlibat.\n\n"
    "Ke depan, kegiatan serupa akan diselenggarakan secara berkala dengan melibatkan lebih banyak "
    "warga dan organisasi otonom seperti Aisyiyah, Pemuda Muhammadiyah, dan IPM.\n\n"
    "(Berita ini adalah contoh fiktif untuk keperluan tugas kuliah Cloud Computing.)"
)


class Command(BaseCommand):
    help = "Isi database dengan konten contoh PCM (fiktif) beserta gambar."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Hapus konten yang ada sebelum mengisi ulang (pesan masuk tidak dihapus).",
        )

    @transaction.atomic
    def handle(self, *args, reset=False, **options):
        if reset:
            for model in [SiteProfile, RelatedLink, Leader, Branch, Institution, Post, Event, Document]:
                model.objects.all().delete()
        elif SiteProfile.objects.exists():
            self.stdout.write(self.style.WARNING("Data sudah ada. Gunakan --reset untuk mengisi ulang."))
            return

        profile = SiteProfile(**PROFILE)
        profile.hero_image.save("hero.jpg", placeholder_image("", (1600, 700)), save=False)
        profile.save()

        for i, (name, url) in enumerate(RELATED_LINKS):
            RelatedLink.objects.create(name=name, url=url, order=i)

        for i, (name, position) in enumerate(LEADERS):
            leader = Leader(name=name, position=position, period="2022–2027", order=i)
            initials = "".join(part[0] for part in name.split()[:2])
            leader.photo.save(f"leader-{i + 1}.jpg", placeholder_image(initials, (600, 600), PALETTE[i % 6]), save=False)
            leader.save()

        for name, chair, address in BRANCHES:
            Branch.objects.create(name=name, chair=chair, address=address, phone="0812-0000-0000")

        for i, (name, category, description) in enumerate(INSTITUTIONS):
            item = Institution(name=name, category=category, description=description, address="Kartasura, Sukoharjo")
            item.image.save(f"aum-{i + 1}.jpg", placeholder_image(name.replace(" ", "\n", 2), color=PALETTE[i % 6]), save=False)
            item.save()

        now = timezone.now()
        for i, (title, lead) in enumerate(POSTS):
            post = Post(title=title, excerpt=lead, body=BODY.format(lead=lead), published_at=now - timedelta(days=4 * i + 1))
            post.cover_image.save(f"berita-{i + 1}.jpg", placeholder_image(f"Berita #{i + 1}", color=PALETTE[i % 6]), save=False)
            post.save()

        for title, days, location, description in EVENTS:
            starts_at = timezone.localtime(now + timedelta(days=days)).replace(hour=8, minute=0, second=0, microsecond=0)
            Event.objects.create(title=title, starts_at=starts_at, location=location, description=description)

        document = Document(title="Program Kerja PCM 2022–2027", description="Ringkasan program kerja (contoh, PDF).")
        document.file.save("program-kerja.pdf", placeholder_image("Program Kerja\nPCM Kartasura\n(contoh)", (1240, 1754), "#ffffff", "PDF"), save=False)
        document.save()

        self.stdout.write(self.style.SUCCESS("Konten contoh berhasil dibuat."))
