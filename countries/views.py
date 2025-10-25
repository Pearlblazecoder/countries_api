from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db.models import Q
from django.http import HttpResponse
import os

from .models import Country
from .serializers import CountrySerializer
from .utils import CountryDataFetcher, ExternalAPIError, SummaryImageGenerator
from django.conf import settings

class RefreshCountriesView(APIView):
    """
    POST /countries/refresh
    Refresh countries data from external APIs
    """
    def post(self, request):
        try:
            print("Starting countries refresh...")
            fetcher = CountryDataFetcher()
            result = fetcher.refresh_countries_data()
            
            # Generate summary image after refresh
            image_generator = SummaryImageGenerator()
            image_generator.generate_summary_image()
            
            response_data = {
                'message': 'Countries data refreshed successfully',
                'countries_processed': result['processed'],
                'countries_updated': result['updated'],
                'countries_created': result['created'],
                'validation_errors': result.get('validation_errors', 0)
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ExternalAPIError as e:
            return Response({
                'error': 'External data source unavailable',
                'details': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CountriesListView(generics.ListAPIView):
    """
    GET /countries
    Get all countries with filtering and sorting using ListAPIView
    """
    serializer_class = CountrySerializer
    
    def get_queryset(self):
        queryset = Country.objects.all()
        
        # Apply filters
        region = self.request.query_params.get('region')
        if region:
            queryset = queryset.filter(region__iexact=region)
        
        currency = self.request.query_params.get('currency')
        if currency:
            queryset = queryset.filter(currency_code__iexact=currency)
        
        # Apply sorting
        sort_by = self.request.query_params.get('sort')
        if sort_by == 'gdp_desc':
            queryset = queryset.exclude(estimated_gdp__isnull=True).order_by('-estimated_gdp')
        elif sort_by == 'gdp_asc':
            queryset = queryset.exclude(estimated_gdp__isnull=True).order_by('estimated_gdp')
        elif sort_by == 'population_desc':
            queryset = queryset.order_by('-population')
        elif sort_by == 'population_asc':
            queryset = queryset.order_by('population')
        elif sort_by == 'name_asc':
            queryset = queryset.order_by('name')
        elif sort_by == 'name_desc':
            queryset = queryset.order_by('-name')
        else:
            queryset = queryset.order_by('name')
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Return array instead of paginated response
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class CountryDetailView(APIView):
    """
    GET /countries/:name
    GET and DELETE operations for specific country
    """
    def get_object(self, name):
        try:
            return Country.objects.get(name__iexact=name)
        except Country.DoesNotExist:
            raise NotFound('Country not found')
    
    def get(self, request, name):
        try:
            country = self.get_object(name)
            serializer = CountrySerializer(country)
            return Response(serializer.data)
        except NotFound as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, name):
        try:
            country = self.get_object(name)
            country.delete()
            return Response({
                'message': f'Country {name} deleted successfully'
            }, status=status.HTTP_200_OK)
        except NotFound as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_404_NOT_FOUND)

class StatusView(APIView):
    """
    GET /status
    Get API status and statistics
    """
    def get(self, request):
        total_countries = Country.objects.count()
        
        last_refresh_country = Country.objects.order_by('-last_refreshed_at').first()
        last_refreshed_at = last_refresh_country.last_refreshed_at if last_refresh_country else None
        
        status_data = {
            'total_countries': total_countries,
            'last_refreshed_at': last_refreshed_at
        }
        
        return Response(status_data)

class CountriesImageView(APIView):
    """
    GET /countries/image
    Serve the generated summary image
    """
    def get(self, request):
        image_path = os.path.join(settings.CACHE_DIR, 'summary.png')
        
        if not os.path.exists(image_path):
            return Response({
                'error': 'Summary image not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            with open(image_path, 'rb') as f:
                return HttpResponse(f.read(), content_type='image/png')
        except Exception as e:
            return Response({
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Simple validation test endpoint
class ValidationTestView(APIView):
    """
    POST /validate-test
    Test validation rules using the CountrySerializer
    """
    def post(self, request):
        serializer = CountrySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'message': 'Validation passed'
        }, status=status.HTTP_200_OK)