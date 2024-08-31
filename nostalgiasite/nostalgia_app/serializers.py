from rest_framework import serializers
from .models import Category, InformationItem, SignificantEvent, Book

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class InformationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InformationItem
        fields = ['id', 'title', 'description', 'year', 'category', 'is_outdated', 'current_status', 'change_description', 'relevance_explanation']

class SignificantEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignificantEvent
        fields = ['id', 'title', 'description', 'year', 'impact']

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'description', 'year', 'category', 'relevance']