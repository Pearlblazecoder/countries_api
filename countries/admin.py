from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Country

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'population', 'currency_code', 'estimated_gdp', 'last_refreshed_at']
    list_filter = ['region', 'currency_code']
    search_fields = ['name', 'capital']
    readonly_fields = ['last_refreshed_at']