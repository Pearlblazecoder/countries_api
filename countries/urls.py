from django.urls import path
from . import views

urlpatterns = [
    path('countries/refresh', views.RefreshCountriesView.as_view(), name='refresh-countries'),
    path('countries/image', views.CountriesImageView.as_view(), name='countries-image'),
    path('countries/status', views.StatusView.as_view(), name='status'),
    path('countries/<str:name>', views.CountryDetailView.as_view(), name='country-by-name'),
    path('countries', views.CountriesListView.as_view(), name='get-countries'),
]