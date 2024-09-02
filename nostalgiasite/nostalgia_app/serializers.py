from rest_framework import serializers
from .models import Category, UserSubmittedFact, APIFact
import logging

logger = logging.getLogger(__name__)

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
    fact_type = serializers.CharField(required=False)

    def to_representation(self, instance):
        try:
            if isinstance(instance, dict):
                # If instance is already a dict, use it directly
                data = instance
            else:
                # Otherwise, serialize the instance
                data = super().to_representation(instance)

            # Set fact_type based on the instance type
            if isinstance(instance, UserSubmittedFact):
                data['fact_type'] = 'user_submitted'
            elif isinstance(instance, APIFact):
                data['fact_type'] = 'api'
            else:
                data['fact_type'] = 'unknown'

            return data
        except Exception as e:
            logger.error(f"Error in CombinedFactSerializer.to_representation: {str(e)}")
            # Return a minimal representation to avoid breaking the entire response
            return {
                'id': getattr(instance, 'id', None),
                'year': getattr(instance, 'year', None),
                'title': getattr(instance, 'title', 'Error retrieving fact'),
                'description': 'An error occurred while processing this fact.',
                'categories': [],
                'source_url': '',
                'fact_type': 'error'
            }