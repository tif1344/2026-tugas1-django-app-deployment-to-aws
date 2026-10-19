from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class SiteProfile(models.Model):
    """Organisation profile. Only one row is expected (enforced in admin)."""

    name = models.CharField("nama organisasi", max_length=150)
    short_name = models.CharField("nama singkat", max_length=50)
    tagline = models.CharField(max_length=200, blank=True)
    about = models.TextField("tentang", blank=True)
    history = models.TextField("sejarah", blank=True)
    vision = models.TextField("visi", blank=True)
    mission = models.TextField("misi", blank=True, help_text="Tulis satu misi per baris.")
    address = models.CharField("alamat", max_length=255, blank=True)
    phone = models.CharField("telepon", max_length=30, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to="profile/", blank=True)
    hero_image = models.ImageField("gambar utama", upload_to="profile/", blank=True)

    class Meta:
        verbose_name = "profil organisasi"
        verbose_name_plural = "profil organisasi"

    def __str__(self):
        return self.name

    @property
    def mission_items(self):
        return [line.strip() for line in self.mission.splitlines() if line.strip()]


class RelatedLink(models.Model):
    """Links to other levels of the Persyarikatan (PDM, PWM, PP), shown in the footer."""

    name = models.CharField("nama", max_length=120)
    url = models.URLField("alamat website")
    order = models.PositiveIntegerField("urutan", default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "tautan terkait"
        verbose_name_plural = "tautan terkait"

    def __str__(self):
        return self.name


class Leader(models.Model):
    name = models.CharField("nama", max_length=120)
    position = models.CharField("jabatan", max_length=120)
    period = models.CharField("periode", max_length=20, blank=True, help_text="Contoh: 2022–2027")
    photo = models.ImageField("foto", upload_to="leaders/", blank=True)
    order = models.PositiveIntegerField("urutan", default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "pimpinan"
        verbose_name_plural = "pimpinan"

    def __str__(self):
        return f"{self.name} — {self.position}"


class Branch(models.Model):
    """Pimpinan Ranting Muhammadiyah (PRM) under this PCM."""

    name = models.CharField("nama ranting", max_length=120)
    chair = models.CharField("ketua", max_length=120, blank=True)
    address = models.CharField("alamat", max_length=255, blank=True)
    phone = models.CharField("telepon", max_length=30, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "ranting"
        verbose_name_plural = "ranting"

    def __str__(self):
        return self.name


class Institution(models.Model):
    """Amal Usaha Muhammadiyah (AUM): schools, clinics, orphanages, etc."""

    class Category(models.TextChoices):
        EDUCATION = "pendidikan", "Pendidikan"
        HEALTH = "kesehatan", "Kesehatan"
        SOCIAL = "sosial", "Sosial"
        ECONOMY = "ekonomi", "Ekonomi"

    name = models.CharField("nama", max_length=150)
    category = models.CharField("bidang", max_length=20, choices=Category.choices)
    description = models.TextField("deskripsi", blank=True)
    address = models.CharField("alamat", max_length=255, blank=True)
    image = models.ImageField("gambar", upload_to="institutions/", blank=True)

    class Meta:
        ordering = ["category", "name"]
        verbose_name = "amal usaha"
        verbose_name_plural = "amal usaha"

    def __str__(self):
        return self.name


class PublishedPostManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True, published_at__lte=timezone.now())


class Post(models.Model):
    title = models.CharField("judul", max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    excerpt = models.CharField("ringkasan", max_length=300, blank=True)
    body = models.TextField("isi")
    cover_image = models.ImageField("gambar sampul", upload_to="posts/%Y/%m/", blank=True)
    published_at = models.DateTimeField("tanggal terbit", default=timezone.now)
    is_published = models.BooleanField("terbitkan", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    published = PublishedPostManager()

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "berita"
        verbose_name_plural = "berita"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "berita"
            slug, n = base, 2
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("website:post_detail", args=[self.slug])


class Event(models.Model):
    title = models.CharField("nama kegiatan", max_length=200)
    starts_at = models.DateTimeField("waktu mulai")
    location = models.CharField("tempat", max_length=200)
    description = models.TextField("keterangan", blank=True)

    class Meta:
        ordering = ["starts_at"]
        verbose_name = "agenda"
        verbose_name_plural = "agenda"

    def __str__(self):
        return self.title


class Document(models.Model):
    title = models.CharField("judul", max_length=200)
    description = models.CharField("keterangan", max_length=300, blank=True)
    file = models.FileField("berkas", upload_to="documents/")
    uploaded_at = models.DateTimeField("diunggah", auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "dokumen"
        verbose_name_plural = "dokumen"

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    name = models.CharField("nama", max_length=120)
    email = models.EmailField()
    subject = models.CharField("subjek", max_length=200)
    message = models.TextField("pesan")
    created_at = models.DateTimeField("dikirim", auto_now_add=True)
    is_read = models.BooleanField("sudah dibaca", default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "pesan masuk"
        verbose_name_plural = "pesan masuk"

    def __str__(self):
        return f"{self.subject} — {self.name}"
