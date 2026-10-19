from .models import RelatedLink, SiteProfile


def site_profile(request):
    return {
        "site_profile": SiteProfile.objects.first(),
        "related_links": RelatedLink.objects.all(),
    }
