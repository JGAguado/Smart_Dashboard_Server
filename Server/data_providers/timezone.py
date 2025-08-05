#!/usr/bin/env python3
"""
Timezone Provider for Smart Dashboard Server.

Handles timezone detection, UTC offset calculation, and local time formatting.
"""

import pytz
from typing import Tuple
from datetime import datetime


class TimezoneProvider:
    """
    Timezone provider for converting coordinates to local time.
    
    Features:
    - City/country to timezone mapping
    - Coordinate-based timezone estimation
    - UTC offset calculation
    - Local datetime formatting
    """
    
    # Simple timezone mapping for common cities/countries
    TIMEZONE_MAPPING = {
        # European cities
        'vienna': 'Europe/Vienna',
        'austria': 'Europe/Vienna',
        'berlin': 'Europe/Berlin', 
        'germany': 'Europe/Berlin',
        'paris': 'Europe/Paris',
        'france': 'Europe/Paris',
        'london': 'Europe/London',
        'uk': 'Europe/London',
        'united kingdom': 'Europe/London',
        'madrid': 'Europe/Madrid',
        'spain': 'Europe/Madrid',
        'rome': 'Europe/Rome',
        'italy': 'Europe/Rome',
        
        # American cities
        'new york': 'America/New_York',
        'usa': 'America/New_York',
        'united states': 'America/New_York',
        'los angeles': 'America/Los_Angeles',
        'chicago': 'America/Chicago',
        'miami': 'America/New_York',
        
        # Asian cities
        'tokyo': 'Asia/Tokyo',
        'japan': 'Asia/Tokyo',
        'beijing': 'Asia/Shanghai',
        'china': 'Asia/Shanghai',
        'seoul': 'Asia/Seoul',
        'south korea': 'Asia/Seoul',
        'mumbai': 'Asia/Kolkata',
        'india': 'Asia/Kolkata',
        
        # Other cities
        'sydney': 'Australia/Sydney',
        'australia': 'Australia/Sydney',
        'moscow': 'Europe/Moscow',
        'russia': 'Europe/Moscow',
        'cairo': 'Africa/Cairo',
        'egypt': 'Africa/Cairo',
        'dubai': 'Asia/Dubai',
        'uae': 'Asia/Dubai',
    }
    
    def estimate_timezone_from_coordinates(self, lat: float, lng: float) -> Tuple[str, str]:
        """
        Estimate timezone from coordinates using longitude-based calculation.
        This is a fallback method when no mapping is available.
        
        Args:
            lat: Latitude (not used in estimation, but kept for interface consistency)
            lng: Longitude
            
        Returns:
            Tuple of (timezone_name, utc_offset_string)
        """
        # Basic estimation: UTC offset = longitude / 15
        utc_offset_hours = round(lng / 15)
        utc_offset_hours = max(-12, min(12, utc_offset_hours))  # Clamp to valid range
        
        if utc_offset_hours == 0:
            timezone_name = "UTC"
            offset_str = "±0"
        else:
            # Create a generic timezone name
            timezone_name = f"Etc/GMT{-utc_offset_hours:+d}"
            offset_str = f"{utc_offset_hours:+d}" if utc_offset_hours != 0 else "±0"
        
        return timezone_name, offset_str
    
    def get_timezone_for_location(self, city: str = None, country: str = None, 
                                lat: float = None, lng: float = None, 
                                cached_timezone: str = None, cached_offset: str = None) -> Tuple[str, str]:
        """
        Get timezone and UTC offset for a location.
        
        Args:
            city: City name (optional)
            country: Country name (optional)
            lat: Latitude (used for coordinate-based estimation)
            lng: Longitude (used for coordinate-based estimation)
            cached_timezone: Previously cached timezone (optional)
            cached_offset: Previously cached UTC offset (optional)
            
        Returns:
            Tuple of (timezone_name, utc_offset_string)
        """
        # Use cached data if available
        if cached_timezone and cached_offset:
            print(f"🕐 Found cached timezone: {cached_timezone} (UTC{cached_offset})")
            return cached_timezone, cached_offset

        try:
            # Try to find timezone using city/country mapping
            timezone_name = None
            
            if city and country:
                # Check city first, then country
                city_lower = city.lower().strip()
                country_lower = country.lower().strip()
                
                if city_lower in self.TIMEZONE_MAPPING:
                    timezone_name = self.TIMEZONE_MAPPING[city_lower]
                elif country_lower in self.TIMEZONE_MAPPING:
                    timezone_name = self.TIMEZONE_MAPPING[country_lower]

            # If no mapping found, estimate from coordinates
            if timezone_name is None:
                if lat is not None and lng is not None:
                    timezone_name, offset_str = self.estimate_timezone_from_coordinates(lat, lng)
                    print(f"⚠️  Using estimated timezone based on coordinates: {timezone_name} (UTC{offset_str})")
                    return timezone_name, offset_str
                else:
                    # Final fallback to UTC
                    print("⚠️  No location data available, using UTC")
                    return "UTC", "±0"

            # Calculate UTC offset using the mapped timezone
            try:
                # Use pytz as primary method (more reliable)
                timezone = pytz.timezone(timezone_name)
                now = datetime.now(timezone)

                # Get UTC offset in seconds and convert to hours
                utc_offset_seconds = now.utcoffset().total_seconds()
                utc_offset_hours = int(utc_offset_seconds / 3600)

                # Format offset string
                if utc_offset_hours == 0:
                    offset_str = "±0"
                elif utc_offset_hours > 0:
                    offset_str = f"+{utc_offset_hours}"
                else:
                    offset_str = str(utc_offset_hours)

                print(f"🕐 Timezone determined: {timezone_name} (UTC{offset_str})")
                return timezone_name, offset_str

            except Exception as e:
                print(f"⚠️  Error calculating offset for {timezone_name}: {e}")
                # Fallback to coordinate estimation
                if lat is not None and lng is not None:
                    return self.estimate_timezone_from_coordinates(lat, lng)
                else:
                    return "UTC", "±0"

        except Exception as e:
            print(f"⚠️  Error determining timezone: {e}")
            if lat is not None and lng is not None:
                return self.estimate_timezone_from_coordinates(lat, lng)
            else:
                return "UTC", "±0"
    
    def get_local_datetime(self, timezone_name: str) -> Tuple[str, str]:
        """
        Get formatted local date and time for a timezone.
        
        Args:
            timezone_name: Timezone name (e.g., 'Europe/Vienna')
            
        Returns:
            Tuple of (date_string, time_string)
        """
        try:
            # Use pytz for timezone handling
            timezone = pytz.timezone(timezone_name)
            local_time = datetime.now(timezone)

            # Format: "03 August" instead of "03/01/2025"
            date_str = local_time.strftime("%d %B")
            time_str = local_time.strftime("%H:%M")

            return date_str, time_str

        except Exception as e:
            print(f"⚠️  Could not get local time for {timezone_name}: {e}")
            # Fallback to UTC
            utc_time = datetime.utcnow()
            date_str = utc_time.strftime("%d %B")
            time_str = utc_time.strftime("%H:%M")
            return date_str, time_str
