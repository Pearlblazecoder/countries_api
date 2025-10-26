from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db.models import Q
from django.http import HttpResponse
import os

from .models import Country, GlobalSettings
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
                'countries_created': result['created']
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

class CountriesListView(APIView):
    """
    GET /countries
    Get all countries with filtering and sorting
    """
    def get(self, request):
        # Define valid query parameters
        valid_params = ['region', 'currency', 'sort']
        provided_params = request.query_params.keys()
        
        # Check for invalid parameters
        invalid_params = [param for param in provided_params if param not in valid_params]
        if invalid_params:
            return Response({
                'error': 'Invalid query parameters',
                'invalid_parameters': invalid_params,
                'valid_parameters': valid_params
            }, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = Country.objects.all()
        
        # Apply filters for valid parameters
        region = request.query_params.get('region')
        if region:
            queryset = queryset.filter(region__iexact=region)
        
        currency = request.query_params.get('currency')
        if currency:
            queryset = queryset.filter(currency_code__iexact=currency)
        
        # Apply sorting
        sort_by = request.query_params.get('sort')
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
        
        serializer = CountrySerializer(queryset, many=True)
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
        try:
            global_refresh = GlobalSettings.objects.get(key='last_global_refresh')
            last_refreshed_at = global_refresh.last_updated
        except GlobalSettings.DoesNotExist:
            last_refreshed_at = None
        
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