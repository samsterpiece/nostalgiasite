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
    list_display = ('title', 'year', 'user', 'status', 'submitted_at')
    list_filter = ('status', 'year', 'categories')
    search_fields = ('title', 'description', 'user__username')
    actions = ['approve_facts', 'deny_facts', 'mark_as_under_review']

    def approve_facts(self, request, queryset):
        queryset.update(status='approved')
    approve_facts.short_description = "Mark selected facts as approved"

    def deny_facts(self, request, queryset):
        queryset.update(status='denied')
    deny_facts.short_description = "Mark selected facts as denied"

    def mark_as_under_review(self, request, queryset):
        queryset.update(status='under_review')
    mark_as_under_review.short_description = "Mark selected facts as under review"