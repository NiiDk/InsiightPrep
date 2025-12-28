# shop/models.py

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth.models import User
import uuid
import datetime

def get_current_year():
    return datetime.date.today().year

# --- 1. User Profile ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# --- 2. Class (Grade) Model ---
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


# --- 3. Term Model ---
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


# --- 4. Subject Model ---
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


# --- 5. QuestionPaper Model ---
class QuestionPaper(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    class_level = models.ForeignKey(Classes, related_name='papers', on_delete=models.PROTECT)
    term = models.ForeignKey(Term, related_name='papers', on_delete=models.PROTECT)
    subject = models.ForeignKey(Subject, related_name='papers', on_delete=models.PROTECT)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    year = models.IntegerField(default=timezone.now().year)
    exam_type = models.CharField(
        max_length=50,
        choices=[
            ('midterm', 'Mid-Term Exam'),
            ('endterm', 'End-Term Exam'),
            ('cat', 'CAT'),
            ('assignment', 'Assignment'),
            ('final', 'Final Exam'),
            ('mock', 'Mock Exam'),
            ('others', 'Others'),
        ],
        default='endterm'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    pdf_file = models.FileField(upload_to='question_papers/', max_length=500)
    password = models.CharField(max_length=50, blank=True)
    is_paid = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    file_size = models.CharField(max_length=20, blank=True, editable=False)
    pages = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.IntegerField(default=0)
    
    class Meta:
        ordering = ('class_level', 'term', 'subject', 'title')
        verbose_name = 'Question Paper'
        verbose_name_plural = 'Question Papers'

    def __str__(self):
        return f"{self.class_level.name} - {self.term.name} - {self.subject.name} ({self.title})"

    def delete(self, *args, **kwargs):
        if self.pdf_file:
            self.pdf_file.delete(save=False)
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = f"{self.class_level.name} {self.term.name} {self.subject.name} {self.title}"
            candidate = slugify(base)
            if not candidate:
                candidate = str(uuid.uuid4())[:12]
            original_candidate = candidate
            counter = 1
            while QuestionPaper.objects.filter(slug=candidate).exists():
                candidate = f"{original_candidate}-{counter}"
                counter += 1
            self.slug = candidate

        if not self.password and self.is_paid:
            self.password = f"INSIGHT_{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:paper_detail', args=[self.class_level.slug, self.term.slug, self.subject.slug, self.slug])

    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])

    def get_pdf_url(self):
        return self.pdf_file.url if self.pdf_file else None
    
    def get_secure_pdf_url(self):
        return self.get_pdf_url()
    
    @property
    def file_name(self):
        return self.pdf_file.name.split('/')[-1] if self.pdf_file else "question_paper.pdf"
    
    @property
    def is_free(self):
        return self.price == 0 or not self.is_paid


# --- 6. Order Model ---
class Order(models.Model):
    user = models.ForeignKey(User, related_name='orders', on_delete=models.SET_NULL, null=True, blank=True)
    ref = models.CharField(max_length=20, unique=True)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    verified = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.ref} - {self.email}"

    def save(self, *args, **kwargs):
        if not self.ref:
            self.ref = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def amount_in_pesewas(self):
        return int(self.total_amount * 100)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    paper = models.ForeignKey(QuestionPaper, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.paper.title} in Order {self.order.ref}"


# --- 7. Legacy Payment Model (Optional cleanup later) ---
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
    
    def amount_in_pesewas(self):
        price = self.amount_paid if self.amount_paid is not None else self.question_paper.price
        return int(price * 100) if price is not None else 0

    def save(self, *args, **kwargs):
        if not self.ref:
            self.ref = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def mark_as_verified(self, transaction_id=None, amount=None):
        self.verified = True
        if transaction_id:
            self.transaction_id = str(transaction_id)
        if amount is not None:
            self.amount_paid = float(amount)
        self.save()

    class Meta:
        ordering = ('-date_created',)


# --- 8. Paper Download History ---
class DownloadHistory(models.Model):
    paper = models.ForeignKey(QuestionPaper, related_name='downloads', on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, related_name='downloads', on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(Order, related_name='downloads', on_delete=models.SET_NULL, null=True, blank=True)
    user_email = models.EmailField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def log_download(cls, paper, email=None, request=None, payment=None, order=None):
        ip = None
        ua = None
        if request is not None:
            xff = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')
            ua = request.META.get('HTTP_USER_AGENT', '')

        return cls.objects.create(
            paper=paper,
            payment=payment,
            order=order,
            user_email=email,
            ip_address=ip,
            user_agent=ua or ''
        )


# --- 9. FREE SAMPLE Model ---
class FreeSample(models.Model):
    question_paper = models.OneToOneField(QuestionPaper, related_name='free_sample', on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    sample_pdf = models.FileField(upload_to='free_samples/', blank=True, null=True)
    downloads = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def delete(self, *args, **kwargs):
        if self.sample_pdf:
            self.sample_pdf.delete(save=False)
        super().delete(*args, **kwargs)
    
    class Meta:
        ordering = ('-created_at',)
