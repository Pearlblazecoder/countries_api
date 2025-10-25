from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from django.db.models import Q
from django.http import HttpResponse
import os

from .models import Country
from .serializers import CountrySerializer, RefreshResponseSerializer, StatusSerializer
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
            image_path = image_generator.generate_summary_image()
            
            response_data = {
                'message': 'Countries data refreshed successfully',
                'countries_processed': result['processed'],
                'countries_updated': result['updated'],
                'countries_created': result['created'],
                'errors': result.get('errors', 0)
            }
            
            if image_path:
                response_data['image_generated'] = True
            else:
                response_data['image_generated'] = False
            
            serializer = RefreshResponseSerializer(data=response_data)
            serializer.is_valid(raise_exception=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ExternalAPIError as e:
            return Response({
                'error': 'External data source unavailable',
                'details': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            return Response({
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CountriesListView(generics.ListAPIView):
    """
    GET /countries
    Get all countries with filtering and sorting using ListAPIView
    """
    serializer_class = CountrySerializer
    
    def get_queryset(self):
        queryset = Country.objects.all()
        
        # Get all valid query parameters
        valid_params = ['region', 'currency', 'sort', 'name']
        provided_params = self.request.query_params.keys()
        
        # Check for invalid parameters
        invalid_params = [param for param in provided_params if param not in valid_params]
        if invalid_params:
            # Return empty queryset for invalid parameters
            return Country.objects.none()
        
        # Apply filters for valid parameters
        region = self.request.query_params.get('region')
        if region:
            queryset = queryset.filter(region__iexact=region)
        
        currency = self.request.query_params.get('currency')
        if currency:
            queryset = queryset.filter(currency_code__iexact=currency)
        
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__iexact=name)
        
        # Apply sorting
        sort_by = self.request.query_params.get('sort')
        sorting_map = {
            'gdp_desc': '-estimated_gdp',
            'gdp_asc': 'estimated_gdp',
            'population_desc': '-population',
            'population_asc': 'population',
            'name_asc': 'name',
            'name_desc': '-name',
        }
        
        if sort_by in sorting_map:
            if sort_by in ['gdp_desc', 'gdp_asc']:
                queryset = queryset.exclude(estimated_gdp__isnull=True)
            queryset = queryset.order_by(sorting_map[sort_by])
        else:
            queryset = queryset.order_by('name')
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Check for invalid parameters before processing
        valid_params = ['region', 'currency', 'sort', 'name']
        provided_params = request.query_params.keys()
        invalid_params = [param for param in provided_params if param not in valid_params]
        
        if invalid_params:
            return Response({
                "error": "Invalid query parameters",
                "invalid_parameters": invalid_params,
                "valid_parameters": valid_params
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return super().list(request, *args, **kwargs)

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
        country = self.get_object(name)
        serializer = CountrySerializer(country)
        return Response(serializer.data)
    
    def delete(self, request, name):
        country = self.get_object(name)
        country.delete()
        return Response({
            'message': f'Country {name} deleted successfully'
        }, status=status.HTTP_200_OK)

class StatusView(generics.ListAPIView):
    """
    GET /status
    Get API status and statistics using ListAPIView
    """
    serializer_class = StatusSerializer
    
    def get_queryset(self):
        # Since this is not a model-based view, return a dummy queryset
        return [None]
    
    def list(self, request, *args, **kwargs):
        total_countries = Country.objects.count()
        
        last_refresh_country = Country.objects.order_by('-last_refreshed_at').first()
        last_refreshed_at = last_refresh_country.last_refreshed_at if last_refresh_country else None
        
        status_data = {
            'total_countries': total_countries,
            'last_refreshed_at': last_refreshed_at
        }
        
        serializer = self.get_serializer(status_data)
        return Response(serializer.data)

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
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)