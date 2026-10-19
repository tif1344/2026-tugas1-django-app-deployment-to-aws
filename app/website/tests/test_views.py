import io
import shutil
import tempfile
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from website.models import ContactMessage, Post

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
@mock.patch("website.deployment.ec2_metadata", return_value=None)
class PublicPagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_pcm", stdout=io.StringIO())

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def test_pages_render(self, _):
        names = ["home", "profile", "leaders", "branches", "institutions", "post_list", "events", "documents", "contact", "status"]
        for name in names:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(f"website:{name}")).status_code, 200)

    def test_post_detail(self, _):
        post = Post.published.first()
        response = self.client.get(post.get_absolute_url())
        self.assertContains(response, post.title)

    def test_unpublished_post_is_hidden(self, _):
        post = Post.objects.create(title="Draf", body="x", is_published=False)
        self.assertEqual(self.client.get(post.get_absolute_url()).status_code, 404)

    def test_seed_creates_media_files(self, _):
        post = Post.objects.first()
        self.assertTrue(post.cover_image.storage.exists(post.cover_image.name))

    def test_contact_form_saves_message(self, _):
        response = self.client.post(
            reverse("website:contact"),
            {"name": "Budi", "email": "budi@example.com", "subject": "Halo", "message": "Tes pesan"},
            follow=True,
        )
        self.assertContains(response, "pesan Anda sudah kami terima")
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_footer_links_to_persyarikatan_sites(self, _):
        response = self.client.get(reverse("website:home"))
        for url in ["https://pdmsukoharjo.or.id", "https://pwmjateng.com", "https://muhammadiyah.or.id"]:
            self.assertContains(response, f'href="{url}"')

    def test_status_page_reports_level_1(self, _):
        self.assertContains(self.client.get(reverse("website:status")), "Level 1 terdeteksi")

    @override_settings(STATUS_PAGE_ENABLED=False)
    def test_status_page_can_be_disabled(self, _):
        self.assertEqual(self.client.get(reverse("website:status")).status_code, 404)
