import requests
import random
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Country, GlobalSettings
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings
from decimal import Decimal, ROUND_HALF_UP

class ExternalAPIError(Exception):
    """Custom exception for external API errors"""
    pass

class CountryDataFetcher:
    def __init__(self):
        self.exchange_rates = None
    
    def fetch_countries_data(self):
        """Fetch countries data from external API"""
        try:
            print(f"Fetching countries from: {settings.COUNTRIES_API_URL}")
            response = requests.get(settings.COUNTRIES_API_URL, timeout=30)
            response.raise_for_status()
            data = response.json()
            print(f"Fetched {len(data)} countries")
            return data
        except requests.exceptions.Timeout:
            raise ExternalAPIError("Countries API timeout")
        except requests.exceptions.ConnectionError:
            raise ExternalAPIError("Countries API connection error")
        except requests.exceptions.RequestException as e:
            raise ExternalAPIError(f"Could not fetch data from countries API: {str(e)}")
    
    def fetch_exchange_rates(self):
        """Fetch exchange rates from external API"""
        try:
            print(f"💱 Fetching exchange rates from: {settings.EXCHANGE_RATE_API_URL}")
            response = requests.get(settings.EXCHANGE_RATE_API_URL, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get('result') == 'success':
                self.exchange_rates = data['rates']
                print(f"Fetched {len(self.exchange_rates)} exchange rates")
            else:
                raise ExternalAPIError("Exchange rate API returned error")
        except requests.exceptions.Timeout:
            raise ExternalAPIError("Exchange rates API timeout")
        except requests.exceptions.ConnectionError:
            raise ExternalAPIError("Exchange rates API connection error")
        except requests.exceptions.RequestException as e:
            raise ExternalAPIError(f"Could not fetch data from exchange rates API: {str(e)}")
    
    def get_currency_code(self, currencies):
        """Extract currency code from currencies array - FIRST currency only"""
        if not currencies or len(currencies) == 0:
            return None  
        first_currency = currencies[0]
        return first_currency.get('code')
    
    def get_exchange_rate(self, currency_code):
        """Get exchange rate for currency code"""
        if not currency_code or not self.exchange_rates:
            return None
        
        rate = self.exchange_rates.get(currency_code)
        if rate:
            return Decimal(str(rate)).quantize(Decimal('0.0000000001'), rounding=ROUND_HALF_UP)
        return None  
    
    def refresh_countries_data(self):
        """Main method to refresh all countries data - EXACTLY as per requirements"""
        # Fetch exchange rates first
        self.fetch_exchange_rates()
        
        # Fetch countries data
        countries_data = self.fetch_countries_data()
        
        processed = 0
        created = 0
        updated = 0
        
        with transaction.atomic():
            # Update global refresh timestamp at the start of transaction
            global_settings, _ = GlobalSettings.objects.update_or_create(
                key='last_global_refresh',
                defaults={'value': timezone.now().isoformat()}
            )
            print(f"Global refresh timestamp updated: {global_settings.last_updated}")
            
            for country_data in countries_data:
                try:
                    processed += 1
                    
                  
                    name = country_data.get('name')
                    if not name:
                        continue 
                    
                    population = country_data.get('population', 0)
                    currencies = country_data.get('currencies', [])
                    currency_code = self.get_currency_code(currencies)
                    
                    # IMPLEMENT EXACT CURRENCY HANDLING LOGIC FROM REQUIREMENTS:
                    exchange_rate = None
                    estimated_gdp = None
                    
                    if not currencies or not currency_code:
                        currency_code = None  
                        exchange_rate = None  
                        estimated_gdp = 0     
                    else:
                        exchange_rate = self.get_exchange_rate(currency_code)
                        
                        if exchange_rate is None:
                            estimated_gdp = None  
                        else:
                            
                            random_multiplier = random.uniform(1000, 2000)
                            gdp_value = (population * random_multiplier) / float(exchange_rate)
                            estimated_gdp = Decimal(str(gdp_value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    
                    # REQUIREMENT: Still store the country record (in all cases)
                    country, created_flag = Country.objects.update_or_create(
                        name=name,
                        defaults={
                            'capital': country_data.get('capital'),
                            'region': country_data.get('region'),
                            'population': population,
                            'currency_code': currency_code,  
                            'exchange_rate': exchange_rate,  
                            'estimated_gdp': estimated_gdp,  
                            'flag_url': country_data.get('flag')
                        }
                    )
                    
                    if created_flag:
                        created += 1
                        print(f"Created: {name} (Currency: {currency_code}, GDP: {estimated_gdp})")
                    else:
                        updated += 1
                        print(f"Updated: {name} (Currency: {currency_code}, GDP: {estimated_gdp})")
                        
                except ValidationError as e:
                    print(f"Validation error for {country_data.get('name', 'Unknown')}: {e.message_dict}")
                    continue
                except Exception as e:
                    print(f"Error processing {country_data.get('name', 'Unknown')}: {str(e)}")
                    continue
        
        print(f"🎉 Refresh completed: {processed} processed, {created} created, {updated} updated")
        
        return {
            'processed': processed,
            'created': created,
            'updated': updated
        }

class SummaryImageGenerator:
    def generate_summary_image(self):
        """Generate summary image with country statistics"""
        try:
            print("Generating summary image...")
            # Get data for summary
            total_countries = Country.objects.count()
            top_countries = Country.objects.exclude(estimated_gdp__isnull=True).order_by('-estimated_gdp')[:5]
            
            # Use global refresh timestamp
            try:
                global_refresh = GlobalSettings.objects.get(key='last_global_refresh')
                last_refresh_time = global_refresh.last_updated
            except GlobalSettings.DoesNotExist:
                last_refresh_time = timezone.now()
            
            # Create image
            img_width = 800
            img_height = 600
            image = Image.new('RGB', (img_width, img_height), color=(240, 240, 240))
            draw = ImageDraw.Draw(image)
            
            # Font sizes
            try:
                large_font = ImageFont.truetype("arial.ttf", 32)
                medium_font = ImageFont.truetype("arial.ttf", 24)
                small_font = ImageFont.truetype("arial.ttf", 18)
            except IOError:
                large_font = ImageFont.load_default()
                medium_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Title
            draw.text((50, 50), "Country Data Summary", fill=(0, 100, 200), font=large_font)
            
            # Statistics
            draw.text((50, 120), f"Total Countries: {total_countries}", fill=(0, 0, 0), font=medium_font)
            draw.text((50, 160), f"Last Updated: {last_refresh_time.strftime('%Y-%m-%d %H:%M:%S UTC')}", 
                     fill=(0, 0, 0), font=small_font)
            
            # Top 5 GDP countries
            draw.text((50, 220), "Top 5 Countries by Estimated GDP:", fill=(0, 100, 200), font=medium_font)
            
            y_position = 270
            for i, country in enumerate(top_countries, 1):
                gdp_value = float(country.estimated_gdp) if country.estimated_gdp else 0
                gdp_formatted = f"${gdp_value:,.2f}"
                text = f"{i}. {country.name}: {gdp_formatted}"
                draw.text((70, y_position), text, fill=(0, 0, 0), font=small_font)
                y_position += 35
            
            # Save image
            image_path = os.path.join(settings.CACHE_DIR, 'summary.png')
            image.save(image_path, 'PNG')
            print(f"Summary image saved: {image_path}")
            
            return image_path
            
        except Exception as e:
            print(f"Error generating summary image: {str(e)}")
            return None