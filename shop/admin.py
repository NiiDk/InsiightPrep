# shop/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Classes, Term, Subject, QuestionPaper, 
    Payment, DownloadHistory, FreeSample
)

# --- 1. Admin setup for Hierarchy Models ---
# ... (ClassesAdmin, TermAdmin, SubjectAdmin remain unchanged)

@admin.register(Classes)
class ClassesAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'get_paper_count', 'view_papers_link']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    
    def get_paper_count(self, obj):
        return obj.papers.count()
    get_paper_count.short_description = 'Papers'
    
    def view_papers_link(self, obj):
        count = obj.papers.count()
        url = reverse('admin:shop_questionpaper_changelist') + f'?class_level__id__exact={obj.id}'
        return format_html('<a href="{}">View {} Papers</a>', url, count)
    view_papers_link.short_description = 'Papers Link'


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['class_name', 'name', 'slug', 'get_paper_count', 'view_papers_link']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['class_name']
    search_fields = ['name', 'class_name__name']
    
    def get_paper_count(self, obj):
        return obj.papers.count()
    get_paper_count.short_description = 'Papers'
    
    def view_papers_link(self, obj):
        count = obj.papers.count()
        url = reverse('admin:shop_questionpaper_changelist') + f'?term__id__exact={obj.id}'
        return format_html('<a href="{}">View {} Papers</a>', url, count)
    view_papers_link.short_description = 'Papers Link'


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'get_paper_count', 'view_papers_link']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    
    def get_paper_count(self, obj):
        return obj.papers.count()
    get_paper_count.short_description = 'Papers'
    
    def view_papers_link(self, obj):
        count = obj.papers.count()
        url = reverse('admin:shop_questionpaper_changelist') + f'?subject__id__exact={obj.id}'
        return format_html('<a href="{}">View {} Papers</a>', url, count)
    view_papers_link.short_description = 'Papers Link'


# --- 2. Enhanced Admin setup for QuestionPaper (REVISED: Removed Preview) ---

@admin.register(QuestionPaper)
class QuestionPaperAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'class_level', 'term', 'subject', 
        'price', 'is_paid', 'is_available', 
        'views', 'pdf_download_link' # REMOVED: 'file_preview'
    ]
    list_filter = ['class_level', 'term', 'subject', 'is_paid', 'is_available', 'exam_type']
    list_editable = ['price', 'is_paid', 'is_available']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'description', 'password']
    readonly_fields = [
        'views', 'file_size', 'created_at', 'updated_at', 
        'pdf_preview', 
        'file_info', 
        'download_count', 
        'last_download'
    ]
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description')
        }),
        ('Hierarchy', {
            'fields': ('class_level', 'term', 'subject'),
            'classes': ('collapse',)
        }),
        ('Paper Details', {
            'fields': ('year', 'exam_type', 'pages', 'views'),
            'classes': ('collapse',)
        }),
        ('Pricing & Status', {
            'fields': ('price', 'is_paid', 'is_available', 'password'),
            'classes': ('collapse',)
        }),
        ('Files', {
            # REMOVED: 'preview_image'
            'fields': ('pdf_file', 'file_info', 'pdf_preview'), 
            'classes': ('wide',)
        }),
        ('Statistics', {
            'fields': ('download_count', 'last_download'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # REMOVED: file_preview method
    
    def pdf_download_link(self, obj):
        """Show download link in list display"""
        if obj.pdf_file:
            return format_html(
                '<a href="{}" target="_blank" title="Download PDF">📥</a>',
                obj.get_pdf_url()
            )
        return "No PDF"
    pdf_download_link.short_description = 'PDF'
    
    def pdf_preview(self, obj):
        """Show PDF info and preview in change form (removed image preview logic)"""
        if obj.pdf_file:
            return format_html("""
                <div style="margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                    <strong>PDF File:</strong> {}
                    <br><strong>Size:</strong> {}
                    <br><strong>URL:</strong> <a href="{}" target="_blank">{}</a>
                </div>
            """,
                obj.file_name,
                obj.file_size or 'N/A', 
                obj.get_pdf_url(),
                "Open in new tab",
                # REMOVED: self._get_preview_html(obj) condition
            )
        return "No PDF uploaded"
    pdf_preview.short_description = 'PDF Preview'
    pdf_preview.allow_tags = True
    
    def file_info(self, obj):
        """Show local file storage information"""
        if obj.pdf_file:
            return format_html("""
                <div style="margin: 10px 0; padding: 10px; background: #e8f4fd; border-radius: 5px;">
                    <strong>Local File Path:</strong> {}
                    <br><strong>Storage Type:</strong> FileSystemStorage
                    <br><strong>Folder:</strong> question_papers/ (in MEDIA_ROOT)
                </div>
            """, obj.pdf_file.name)
        return "No file uploaded"
    file_info.short_description = 'File Storage Info'
    
    def download_count(self, obj):
        return obj.downloads.count()
    download_count.short_description = 'Total Downloads'
    
    def last_download(self, obj):
        last = obj.downloads.order_by('-downloaded_at').first()
        if last:
            return last.downloaded_at
        return "Never"
    last_download.short_description = 'Last Downloaded'
    
    # REMOVED: _get_preview_html helper method
    
    def save_model(self, request, obj, form, change):
        # Auto-generate title if not provided
        if not obj.title or obj.title.strip() == '':
            obj.title = f"{obj.subject.name} {obj.get_exam_type_display()} {obj.year}"
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'class_level', 'term', 'subject'
        )


# --- 3. Enhanced Admin setup for Payment ---
# ... (PaymentAdmin remains unchanged)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'ref_short', 'question_paper_link', 'email', 
        'phone_number', 'amount_display', 'verified', 
        'date_created', 'download_link'
    ]
    list_filter = ['verified', 'date_created', 'payment_method']
    search_fields = ['ref', 'email', 'phone_number', 'question_paper__title', 'transaction_id']
    list_editable = ['verified']
    readonly_fields = ['ref', 'date_created', 'transaction_details', 'download_info']
    actions = ['mark_as_verified', 'mark_as_unverified']
    list_per_page = 25
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('ref', 'question_paper', 'amount_paid', 'payment_method', 'transaction_id')
        }),
        ('Customer Information', {
            'fields': ('email', 'phone_number')
        }),
        ('Status', {
            'fields': ('verified', 'date_created')
        }),
        ('Transaction Details', {
            'fields': ('transaction_details',),
            'classes': ('collapse',)
        }),
        ('Download Information', {
            'fields': ('download_info',),
            'classes': ('collapse',)
        }),
    )
    
    def ref_short(self, obj):
        return f"#{obj.ref[:8]}..."
    ref_short.short_description = 'Reference'
    ref_short.admin_order_field = 'ref'
    
    def question_paper_link(self, obj):
        url = reverse('admin:shop_questionpaper_change', args=[obj.question_paper.id])
        return format_html('<a href="{}">{}</a>', url, obj.question_paper.title)
    question_paper_link.short_description = 'Question Paper'
    
    def amount_display(self, obj):
        if obj.amount_paid:
            return f"GH₵{obj.amount_paid}"
        return f"GH₵{obj.question_paper.price}"
    amount_display.short_description = 'Amount'
    
    def download_link(self, obj):
        if obj.verified and obj.question_paper.pdf_file:
            return format_html(
                '<a href="{}" target="_blank" title="Download">📥</a>',
                obj.question_paper.get_pdf_url()
            )
        return "—"
    download_link.short_description = 'Download'
    
    def transaction_details(self, obj):
        return format_html("""
            <div style="padding: 10px; background: #f8f9fa; border-radius: 5px;">
                <strong>Reference:</strong> {}<br>
                <strong>Amount in Pesewas:</strong> {}<br>
                <strong>Paper Price:</strong> GH₵{}<br>
                <strong>Amount Paid:</strong> {}
            </div>
        """,
            obj.ref,
            obj.amount_in_pesewas(),
            obj.question_paper.price,
            f"GH₵{obj.amount_paid}" if obj.amount_paid else "Not recorded"
        )
    transaction_details.short_description = 'Transaction Details'
    
    def download_info(self, obj):
        downloads = obj.downloads.count()
        if downloads > 0:
            last_download = obj.downloads.order_by('-downloaded_at').first()
            return format_html("""
                <div style="padding: 10px; background: #e8f4fd; border-radius: 5px;">
                    <strong>Total Downloads:</strong> {}<br>
                    <strong>Last Download:</strong> {}<br>
                    <strong>By:</strong> {}
                </div>
            """,
                downloads,
                last_download.downloaded_at if last_download else "Never",
                last_download.user_email if last_download else "—"
            )
        return "No downloads yet"
    download_info.short_description = 'Download History'
    
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(verified=True)
        self.message_user(request, f"{updated} payments marked as verified.")
    mark_as_verified.short_description = "Mark selected payments as verified"
    
    def mark_as_unverified(self, request, queryset):
        updated = queryset.update(verified=False)
        self.message_user(request, f"{updated} payments marked as unverified.")
    mark_as_unverified.short_description = "Mark selected payments as unverified"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('question_paper')


# --- 4. Admin setup for DownloadHistory ---
# ... (DownloadHistoryAdmin remains unchanged)

@admin.register(DownloadHistory)
class DownloadHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'paper_link', 'user_email', 'downloaded_at', 
        'ip_address_short', 'payment_link', 'user_agent_short'
    ]
    list_filter = ['downloaded_at', 'paper__class_level', 'paper__subject']
    search_fields = ['user_email', 'paper__title', 'ip_address', 'user_agent']
    readonly_fields = ['downloaded_at', 'all_info']
    date_hierarchy = 'downloaded_at'
    list_per_page = 50
    
    fieldsets = (
        ('Download Information', {
            'fields': ('paper', 'user_email', 'downloaded_at', 'ip_address', 'user_agent')
        }),
        ('Payment Information', {
            'fields': ('payment',),
            'classes': ('collapse',)
        }),
        ('All Information', {
            'fields': ('all_info',),
            'classes': ('collapse',)
        }),
    )
    
    def paper_link(self, obj):
        url = reverse('admin:shop_questionpaper_change', args=[obj.paper.id])
        return format_html('<a href="{}">{}</a>', url, obj.paper.title)
    paper_link.short_description = 'Question Paper'
    paper_link.admin_order_field = 'paper__title'
    
    def ip_address_short(self, obj):
        return obj.ip_address[:15] + "..." if obj.ip_address and len(obj.ip_address) > 15 else obj.ip_address
    ip_address_short.short_description = 'IP Address'
    
    def user_agent_short(self, obj):
        if obj.user_agent:
            ua = obj.user_agent.lower()
            if 'chrome' in ua:
                return 'Chrome'
            elif 'firefox' in ua:
                return 'Firefox'
            elif 'safari' in ua and 'chrome' not in ua:
                return 'Safari'
            elif 'edge' in ua:
                return 'Edge'
            elif 'opera' in ua:
                return 'Opera'
            return ua[:30] + "..."
        return "Unknown"
    user_agent_short.short_description = 'Browser'
    
    def payment_link(self, obj):
        if obj.payment:
            url = reverse('admin:shop_payment_change', args=[obj.payment.id])
            return format_html('<a href="{}">#{}</a>', url, obj.payment.ref[:8])
        return "—"
    payment_link.short_description = 'Payment'
    
    def all_info(self, obj):
        return format_html("""
            <div style="padding: 10px; background: #f5f5f5; border-radius: 5px; font-family: monospace;">
                <strong>User Agent:</strong><br>{}
            </div>
        """, obj.user_agent if obj.user_agent else "Not available")
    all_info.short_description = 'Full User Agent'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('paper', 'payment')


# --- 5. Admin setup for FreeSample ---
# ... (FreeSampleAdmin remains unchanged)

@admin.register(FreeSample)
class FreeSampleAdmin(admin.ModelAdmin):
    list_display = [
        'question_paper_link', 'downloads', 'created_at', 
        'sample_preview', 'sample_download_link'
    ]
    list_filter = ['created_at']
    search_fields = ['question_paper__title', 'description']
    readonly_fields = ['downloads', 'created_at', 'sample_info']
    
    fieldsets = (
        ('Sample Information', {
            'fields': ('question_paper', 'description', 'downloads')
        }),
        ('Sample File', {
            'fields': ('sample_pdf', 'sample_info', 'sample_preview_field'),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def question_paper_link(self, obj):
        url = reverse('admin:shop_questionpaper_change', args=[obj.question_paper.id])
        return format_html('<a href="{}">{}</a>', url, obj.question_paper.title)
    question_paper_link.short_description = 'Question Paper'
    
    def sample_preview(self, obj):
        if obj.sample_pdf:
            return "✅"
        return "❌"
    sample_preview.short_description = 'Has Sample'
    
    def sample_download_link(self, obj):
        if obj.sample_pdf:
            return format_html(
                '<a href="{}" target="_blank" title="Download Sample">📥</a>',
                obj.sample_pdf.url
            )
        return "—"
    sample_download_link.short_description = 'Download'
    
    def sample_info(self, obj):
        if obj.sample_pdf:
            return format_html("""
                <div style="padding: 10px; background: #f0f8ff; border-radius: 5px;">
                    <strong>Sample PDF:</strong> Available<br>
                    <strong>File Path:</strong> {}<br>
                    <strong>URL:</strong> <a href="{}" target="_blank">Open in new tab</a><br>
                    <strong>Downloads:</strong> {} times
                </div>
            """, obj.sample_pdf.name, obj.sample_pdf.url, obj.downloads)
        return "No sample PDF uploaded"
    sample_info.short_description = 'Sample Information'
    
    def sample_preview_field(self, obj):
        if obj.sample_pdf:
            return format_html("""
                <div style="margin-top: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                    <strong>Sample PDF Link:</strong><br>
                    <a href="{}" target="_blank">{}</a>
                </div>
            """, obj.sample_pdf.url, obj.sample_pdf.url)
        return "No sample available"
    sample_preview_field.short_description = 'Sample Link Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('question_paper')


# Optional: Custom admin site header
admin.site.site_header = 'InsightInnovations Administration'
admin.site.site_title = 'InsightInnovations Admin Portal'
admin.site.index_title = 'Welcome to InsightInnovations Admin'