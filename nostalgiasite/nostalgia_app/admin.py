from django.contrib import admin
from .models import Category, InformationItem, SignificantEvent, Book, UserSubmittedFact

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(InformationItem)
class InformationItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'get_categories', 'is_outdated')
    list_filter = ('categories', 'is_outdated', 'year')
    search_fields = ('title', 'description')

    def get_categories(self, obj):
        return ", ".join([category.name for category in obj.categories.all()])
    get_categories.short_description = 'Categories'

@admin.register(SignificantEvent)
class SignificantEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'year')
    list_filter = ('year',)
    search_fields = ('title', 'description', 'impact')

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'year', 'get_categories')
    list_filter = ('categories', 'year')
    search_fields = ('title', 'author', 'description')

    def get_categories(self, obj):
        return ", ".join([category.name for category in obj.categories.all()])
    get_categories.short_description = 'Categories'

@admin.register(UserSubmittedFact)
class UserSubmittedFactAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'user', 'is_approved')
    list_filter = ('is_approved', 'year')
    search_fields = ('title', 'description', 'user__username')
    actions = ['approve_facts']

    def approve_facts(self, request, queryset):
        queryset.update(is_approved=True)
    approve_facts.short_description = "Approve selected facts"