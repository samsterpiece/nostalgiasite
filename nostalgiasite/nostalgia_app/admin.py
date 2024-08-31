from django.contrib import admin
from .models import Category, InformationItem, SignificantEvent, Book

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(InformationItem)
class InformationItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'category', 'is_outdated')
    list_filter = ('category', 'is_outdated', 'year')
    search_fields = ('title', 'description')

@admin.register(SignificantEvent)
class SignificantEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'year')
    list_filter = ('year',)
    search_fields = ('title', 'description', 'impact')

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'year', 'category')
    list_filter = ('category', 'year')
    search_fields = ('title', 'author', 'description')