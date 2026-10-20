from django.contrib import admin

from .models import OCRDocument, OCRJob, OCRPage


class OCRDocumentInline(admin.TabularInline):
    model = OCRDocument
    extra = 0
    fields = ("original_filename", "status", "page_count", "pages_processed", "processing_seconds")
    readonly_fields = fields
    can_delete = False
    show_change_link = True


@admin.register(OCRJob)
class OCRJobAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "language", "documents_count", "created_at", "finished_at")
    list_filter = ("status", "language")
    search_fields = ("title", "id")
    readonly_fields = ("id", "created_at", "started_at", "finished_at")
    inlines = [OCRDocumentInline]


class OCRPageInline(admin.TabularInline):
    model = OCRPage
    extra = 0
    fields = ("number", "blocks_count", "tables_count")
    readonly_fields = fields
    can_delete = False


@admin.register(OCRDocument)
class OCRDocumentAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "job", "status", "language", "page_count", "processing_seconds")
    list_filter = ("status", "language", "mime_type")
    search_fields = ("original_filename", "id")
    readonly_fields = ("id", "created_at", "finished_at")
    inlines = [OCRPageInline]
