from rest_framework import serializers
from .models import Country

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = [
            'id', 'name', 'capital', 'region', 'population',
            'currency_code', 'exchange_rate', 'estimated_gdp',
            'flag_url', 'last_refreshed_at'
        ]
        read_only_fields = ['id', 'last_refreshed_at']
    
    def validate(self, data):
        """
        Custom validation for required fields
        """
        errors = {}
        
        # Required fields validation
        if not data.get('name'):
            errors['name'] = 'is required'
        if data.get('population') is None:
            errors['population'] = 'is required'
        if not data.get('currency_code'):
            errors['currency_code'] = 'is required'
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data

class RefreshResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    countries_processed = serializers.IntegerField()
    countries_updated = serializers.IntegerField()
    countries_created = serializers.IntegerField()
    validation_errors = serializers.IntegerField(required=False)

class StatusSerializer(serializers.Serializer):
    total_countries = serializers.IntegerField()
    last_refreshed_at = serializers.DateTimeField()