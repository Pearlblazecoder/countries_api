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

class RefreshResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    countries_processed = serializers.IntegerField()
    countries_updated = serializers.IntegerField()
    countries_created = serializers.IntegerField()

class StatusSerializer(serializers.Serializer):
    total_countries = serializers.IntegerField()
    last_refreshed_at = serializers.DateTimeField()