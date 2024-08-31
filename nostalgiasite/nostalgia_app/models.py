from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from datetime import datetime
from django.core.exceptions import ValidationError
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class InformationItem(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    year = models.IntegerField()
    categories = models.ManyToManyField(Category, related_name='items')
    is_outdated = models.BooleanField(default=False)
    current_status = models.TextField(blank=True)
    change_description = models.TextField(blank=True)
    relevance_explanation = models.TextField(blank=True)
    source_url = models.URLField(blank=True)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=datetime.now())
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.year} - {self.title}"

class SignificantEvent(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    year = models.IntegerField()
    impact = models.TextField()
    source_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.year} - {self.title}"

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    description = models.TextField()
    year = models.IntegerField()
    categories = models.ManyToManyField(Category, related_name='books')
    relevance = models.TextField()
    isbn = models.CharField(max_length=13, blank=True)
    cover_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.title} by {self.author}"

class UserSubmittedFact(models.Model):
    STATUS_CHOICES = [
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('undetermined', 'Undetermined'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    year = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    categories = models.ManyToManyField(Category)
    source_url = models.URLField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='under_review')
    submitted_at = models.DateTimeField(auto_now_add=True)
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reviewed_facts')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notification_email = models.EmailField(blank=True, null=True)
    notification_phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.year} - {self.title} (Submitted by {self.user.username})"
    
    def clean(self):
        if self.year < 1900 or self.year > timezone.now().year:
            raise ValidationError("Year must be between 1900 and the current year.")
        if not self.notification_email and not self.notification_phone:
            raise ValidationError("Please provide either an email or phone number for notifications.")

        # Allow reviewed_by to be blank during initial submission
        if self.pk is None:
            self._meta.get_field('reviewed_by').blank = True

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)