from django.db import models
from django.core.exceptions import ValidationError
import random

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    capital = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=50, blank=True, null=True)
    population = models.BigIntegerField()
    currency_code = models.CharField(max_length=3, blank=True, null=True)  # Made optional for countries without currency
    exchange_rate = models.DecimalField(max_digits=20, decimal_places=10, blank=True, null=True)
    estimated_gdp = models.DecimalField(max_digits=30, decimal_places=10, blank=True, null=True)
    flag_url = models.URLField(blank=True, null=True)
    last_refreshed_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'countries'
        ordering = ['name']
    
    def clean(self):
        errors = {}
        
        # Required fields validation
        if not self.name:
            errors['name'] = 'is required'
        if self.population is None:
            errors['population'] = 'is required'
        if not self.currency_code:
            errors['currency_code'] = 'is required'
            
        if errors:
            raise ValidationError(errors)
    
    def calculate_estimated_gdp(self):
        """Calculate estimated GDP based on population and exchange rate"""
        if self.population and self.exchange_rate:
            random_multiplier = random.uniform(1000, 2000)
            gdp = (self.population * random_multiplier) / float(self.exchange_rate)
            return round(gdp, 10)
        return None
    
    def save(self, *args, **kwargs):
        # Calculate estimated GDP before saving
        if self.population and self.exchange_rate:
            self.estimated_gdp = self.calculate_estimated_gdp()
        else:
            self.estimated_gdp = None
            
        # Run validation before saving
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name