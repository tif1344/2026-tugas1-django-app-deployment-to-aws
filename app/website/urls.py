from django.urls import path

from . import views

app_name = "website"

urlpatterns = [
    path("", views.home, name="home"),
    path("profil/", views.profile, name="profile"),
    path("pimpinan/", views.leaders, name="leaders"),
    path("ranting/", views.branches, name="branches"),
    path("amal-usaha/", views.institutions, name="institutions"),
    path("berita/", views.post_list, name="post_list"),
    path("berita/<slug:slug>/", views.post_detail, name="post_detail"),
    path("agenda/", views.events, name="events"),
    path("unduhan/", views.documents, name="documents"),
    path("kontak/", views.contact, name="contact"),
    path("status/", views.status, name="status"),
]
