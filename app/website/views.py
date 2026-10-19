from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .deployment import deployment_info
from .forms import ContactForm
from .models import Branch, Document, Event, Institution, Leader, Post


def home(request):
    now = timezone.now()
    return render(
        request,
        "website/home.html",
        {
            "latest_posts": Post.published.all()[:3],
            "upcoming_events": Event.objects.filter(starts_at__gte=now)[:3],
            "leader_count": Leader.objects.count(),
            "institution_count": Institution.objects.count(),
            "branch_count": Branch.objects.count(),
        },
    )


def profile(request):
    return render(request, "website/profile.html")


def leaders(request):
    return render(request, "website/leaders.html", {"leaders": Leader.objects.all()})


def branches(request):
    return render(request, "website/branches.html", {"branches": Branch.objects.all()})


def institutions(request):
    grouped = []
    for value, label in Institution.Category.choices:
        items = Institution.objects.filter(category=value)
        if items:
            grouped.append((label, items))
    return render(request, "website/institutions.html", {"grouped": grouped})


def post_list(request):
    page = Paginator(Post.published.all(), 6).get_page(request.GET.get("page"))
    return render(request, "website/post_list.html", {"page": page})


def post_detail(request, slug):
    post = get_object_or_404(Post.published, slug=slug)
    others = Post.published.exclude(pk=post.pk)[:3]
    return render(request, "website/post_detail.html", {"post": post, "others": others})


def events(request):
    now = timezone.now()
    return render(
        request,
        "website/events.html",
        {
            "upcoming": Event.objects.filter(starts_at__gte=now),
            "past": Event.objects.filter(starts_at__lt=now).order_by("-starts_at")[:10],
        },
    )


def documents(request):
    return render(request, "website/documents.html", {"documents": Document.objects.all()})


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Terima kasih, pesan Anda sudah kami terima.")
        return redirect("website:contact")
    return render(request, "website/contact.html", {"form": form})


def status(request):
    if not settings.STATUS_PAGE_ENABLED:
        raise Http404
    return render(request, "website/status.html", {"info": deployment_info()})
