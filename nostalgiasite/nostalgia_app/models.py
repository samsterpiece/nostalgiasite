from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from datetime import datetime

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    year = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    categories = models.ManyToManyField(Category)
    source_url = models.URLField()
    is_approved = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.year} - {self.title} (Submitted by {self.user.username})"