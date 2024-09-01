from rest_framework import serializers
from .models import Category, UserSubmittedFact, APIFact

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class UserSubmittedFactSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = UserSubmittedFact
        fields = ['id', 'year', 'title', 'description', 'categories', 'source_url', 'status', 'submitted_at']

class APIFactSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = APIFact
        fields = ['id', 'year', 'title', 'description', 'categories', 'source_url', 'created_at', 'updated_at']

class CombinedFactSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    year = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    categories = CategorySerializer(many=True)
    source_url = serializers.URLField()
    fact_type = serializers.CharField()  # To distinguish between UserSubmittedFact and APIFact