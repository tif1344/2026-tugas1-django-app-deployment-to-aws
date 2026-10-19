from django.contrib import admin

from .models import (
    Branch,
    ContactMessage,
    Document,
    Event,
    Institution,
    Leader,
    Post,
    RelatedLink,
    SiteProfile,
)


@admin.register(SiteProfile)
class SiteProfileAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RelatedLink)
class RelatedLinkAdmin(admin.ModelAdmin):
    list_display = ["name", "url", "order"]
    list_editable = ["order"]


@admin.register(Leader)
class LeaderAdmin(admin.ModelAdmin):
    list_display = ["name", "position", "period", "order"]
    list_editable = ["order"]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["name", "chair", "phone"]
    search_fields = ["name", "chair"]


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "address"]
    list_filter = ["category"]
    search_fields = ["name"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "published_at", "is_published"]
    list_filter = ["is_published"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ["title"]}
    date_hierarchy = "published_at"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "starts_at", "location"]
    date_hierarchy = "starts_at"


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "uploaded_at"]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["subject", "name", "email", "created_at", "is_read"]
    list_filter = ["is_read"]
    readonly_fields = ["name", "email", "subject", "message", "created_at"]

    def has_add_permission(self, request):
        return False
