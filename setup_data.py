#!/usr/bin/env python
"""
EGSA Setup Script
Creates initial test data for the EGSA application
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth.models import User
from egsa.models import UtilityReading, UserProfile
from egsa.utils.egsa_calculator import UtilityCalculatorFactory


def create_test_user():
    """Create a test user for demonstration"""
    try:
        user = User.objects.get(username='testuser')
        print("✓ Test user already exists")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        print("✓ Test user created: testuser / testpass123")
    
    # Create user profile
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'phone': '(555) 123-4567',
            'department': 'Facilities Management',
            'notification_preferences': True
        }
    )
    
    if created:
        print("✓ User profile created")
    
    return user


def create_sample_readings(user):
    """Create sample utility readings"""
    print("Creating sample utility readings...")
    
    # Sample data for the last 30 days
    utilities = ['electricity', 'gas', 'steam', 'air_conditioning']
    locations = ['Main Building', 'West Wing', 'East Wing', 'Basement']
    
    reading_count = 0
    
    for i in range(30):  # Last 30 days
        date = datetime.now() - timedelta(days=i)
        
        for utility_type in utilities:
            if i % 3 == 0:  # Create readings every 3 days for variety
                # Generate realistic reading values
                base_values = {
                    'electricity': (300, 800),  # kWh range
                    'gas': (50, 200),           # cubic meter range
                    'steam': (20, 100),         # pounds range
                    'air_conditioning': (100, 400)  # kWh range
                }
                
                min_val, max_val = base_values[utility_type]
                import random
                reading_value = round(random.uniform(min_val, max_val), 2)
                
                # Calculate cost using our custom calculator
                calculator = UtilityCalculatorFactory.create_calculator(utility_type)
                cost = calculator.calculate_cost(reading_value)
                
                # Set appropriate unit
                units = {
                    'electricity': 'kWh',
                    'gas': 'cubic_meter',
                    'steam': 'pounds',
                    'air_conditioning': 'kWh'
                }
                
                unit = units[utility_type]
                location = random.choice(locations)
                
                # Create reading
                reading = UtilityReading.objects.create(
                    user=user,
                    utility_type=utility_type,
                    reading_value=Decimal(str(reading_value)),
                    unit=unit,
                    cost=cost,
                    reading_date=date,
                    location=location,
                    notes=f"Automated reading for {utility_type}" if i % 5 == 0 else ""
                )
                
                reading_count += 1
    
    print(f"✓ Created {reading_count} sample readings")


def main():
    """Main setup function"""
    print("="*50)
    print("EGSA - Utility Management System Setup")
    print("="*50)
    
    # Create test user
    user = create_test_user()
    
    # Create sample readings
    create_sample_readings(user)
    
    print("\n" + "="*50)
    print("SETUP COMPLETE!")
    print("="*50)
    print("You can now:")
    print("1. Login as admin user:")
    print("   Username: admin")
    print("   Password: (the password you set)")
    print()
    print("2. Or login as test user:")
    print("   Username: testuser")
    print("   Password: testpass123")
    print()
    print("3. Start the development server:")
    print("   python manage.py runserver")
    print()
    print("4. Visit: http://127.0.0.1:8000")
    print("="*50)


if __name__ == '__main__':
    main()
