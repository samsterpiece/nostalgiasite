from django.db import models
from django.utils.text import slugify

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
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    is_outdated = models.BooleanField(default=False)
    current_status = models.TextField(blank=True)
    change_description = models.TextField(blank=True)
    relevance_explanation = models.TextField(blank=True)

    def __str__(self):
        return f"{self.year} - {self.title}"

class SignificantEvent(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    year = models.IntegerField()
    impact = models.TextField()

    def __str__(self):
        return f"{self.year} - {self.title}"

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    description = models.TextField()
    year = models.IntegerField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='books')
    relevance = models.TextField()

    def __str__(self):
        return f"{self.title} by {self.author}"