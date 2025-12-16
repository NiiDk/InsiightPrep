from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
import uuid

# --- Helper Functions ---

def get_current_year():
    """Returns the current year as a default for QuestionPaper."""
    return timezone.now().year

# --- 1. Class (Grade) Model ---

class Classes(models.Model):
    name = models.CharField(max_length=100, help_text="e.g., JHS 1, Basic 7")
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Class (Grade)'
        verbose_name_plural = 'Classes (Grades)'
        ordering = ('name',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:term_list', args=[self.slug])

    def get_paper_count(self):
        return self.papers.count()


# --- 2. Term Model ---

class Term(models.Model):
    class_name = models.ForeignKey(Classes, related_name='terms', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, help_text="e.g., Term 1, Term 2")
    slug = models.SlugField(max_length=50)

    class Meta:
        verbose_name_plural = 'Terms'
        unique_together = ('class_name', 'slug')
        ordering = ('name',)

    def __str__(self):
        return f"{self.class_name.name} - {self.name}"

    def get_absolute_url(self):
        return reverse('shop:subject_list', args=[self.class_name.slug, self.slug])

    def get_paper_count(self):
        return self.papers.count()


# --- 3. Subject Model ---

class Subject(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'Subjects'
        ordering = ('name',)

    def __str__(self):
        return self.name

    def get_paper_count(self):
        return self.papers.count()


# --- 4. QuestionPaper Model ---

class QuestionPaper(models.Model):
    # Core Information
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Description of the paper")
    
    # Hierarchy Relationships
    class_level = models.ForeignKey(Classes, related_name='papers', on_delete=models.PROTECT)
    term = models.ForeignKey(Term, related_name='papers', on_delete=models.PROTECT)
    subject = models.ForeignKey(Subject, related_name='papers', on_delete=models.PROTECT)
    
    # Unique identifier - FIXED: Removed lambda to allow migration
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    
    # Paper details - FIXED: Using callable function
    year = models.IntegerField(
        default=get_current_year,
        help_text="Year the paper was administered"
    )
    exam_type = models.CharField(
        max_length=50,
        choices=[
            ('midterm', 'Mid-Term Exam'),
            ('endterm', 'End-Term Exam'),
            ('cat', 'CAT (Continuous Assessment Test)'),
            ('assignment', 'Assignment'),
            ('final', 'Final Exam'),
            ('mock', 'Mock Exam'),
            ('others', 'Others'),
        ],
        default='endterm'
    )
    
    # File and pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    pdf_file = models.FileField(
        upload_to='question_papers/', 
        max_length=500, 
        blank=False,
        null=False,
        help_text="Upload PDF question paper"
    )
    password = models.CharField(max_length=50, blank=True)
    
    # Status flags
    is_paid = models.BooleanField(default=True, help_text="Is this a paid paper or a free sample?")
    is_available = models.BooleanField(default=True, help_text="Is this paper available for purchase?")
    
    # File information
    file_size = models.CharField(max_length=20, blank=True, editable=False)
    pages = models.IntegerField(default=1, help_text="Number of pages")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.IntegerField(default=0, help_text="Number of times viewed")
    
    class Meta:
        ordering = ('class_level', 'term', 'subject', 'title')
        verbose_name = 'Question Paper'
        verbose_name_plural = 'Question Papers'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['class_level', 'term', 'subject']),
            models.Index(fields=['is_available', 'is_paid']),
        ]

    def __str__(self):
        return f"{self.class_level.name} - {self.term.name} - {self.subject.name} ({self.title})"

    def delete(self, *args, **kwargs):
        if self.pdf_file:
            self.pdf_file.delete(save=False)
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            base_slug = slugify(f"{self.class_level.name} {self.term.name} {self.subject.name} {self.title}")
            slug_candidate = base_slug or str(uuid.uuid4())[:8]
            counter = 1
            while QuestionPaper.objects.filter(slug=slug_candidate).exists():
                slug_candidate = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug_candidate
        
        # Set default password if not provided
        if not self.password and self.is_paid:
            self.password = f"INSIGHT_{uuid.uuid4().hex[:8].upper()}"
        
        # Update file size 
        if self.pdf_file and not self.file_size:
            try:
                size_bytes = self.pdf_file.size
                if size_bytes < 1024:
                    self.file_size = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    self.file_size = f"{size_bytes / 1024:.1f} KB"
                else:
                    self.file_size = f"{size_bytes / (1024 * 1024):.1f} MB"
            except Exception:
                pass
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            'shop:paper_detail',
            args=[self.class_level.slug, self.term.slug, self.subject.slug, self.slug]
        )

    @property
    def file_name(self):
        if self.pdf_file:
            return self.pdf_file.name.split('/')[-1]
        return "question_paper.pdf"
    
    @property
    def is_free(self):
        return self.price == 0 or not self.is_paid


# --- 5. Payment Model ---

class Payment(models.Model):
    ref = models.CharField(max_length=20, unique=True)
    question_paper = models.ForeignKey(QuestionPaper, related_name='payments', on_delete=models.PROTECT)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_method = models.CharField(max_length=50, default='paystack')
    transaction_id = models.CharField(max_length=100, blank=True)
    verified = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_created',)

    def __str__(self):
        return f"Payment #{self.ref} - {self.email}"

    def save(self, *args, **kwargs):
        if not self.ref:
            self.ref = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)


# --- 6. Download History ---

class DownloadHistory(models.Model):
    paper = models.ForeignKey(QuestionPaper, related_name='downloads', on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, related_name='downloads', on_delete=models.SET_NULL, null=True, blank=True)
    user_email = models.EmailField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Download Histories'
        ordering = ('-downloaded_at',)

    def __str__(self):
        return f"Download of {self.paper.title} by {self.user_email or 'Anonymous'}"


# --- 7. Free Sample Model ---

class FreeSample(models.Model):
    question_paper = models.OneToOneField(QuestionPaper, related_name='free_sample', on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    sample_pdf = models.FileField(upload_to='free_samples/', blank=True, null=True)
    downloads = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"Free Sample for {self.question_paper.title}"

    def delete(self, *args, **kwargs):
        if self.sample_pdf:
            self.sample_pdf.delete(save=False)
        super().delete(*args, **kwargs)