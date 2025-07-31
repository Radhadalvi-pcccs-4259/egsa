#!/usr/bin/env python
"""
Fix script for EGSA application issues
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth.models import User


def reset_admin_password():
    """Reset admin password"""
    try:
        admin_user = User.objects.get(username='admin')
        admin_user.set_password('admin123')
        admin_user.save()
        print("✓ Admin password reset to: admin123")
    except User.DoesNotExist:
        print("✗ Admin user not found")


def create_simple_admin():
    """Create a simple admin user"""
    try:
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Admin',
                'last_name': 'User'
            }
        )
        
        if created:
            user.set_password('admin123')
            user.save()
            print("✓ Admin user created with password: admin123")
        else:
            user.set_password('admin123')
            user.is_staff = True
            user.is_superuser = True
            user.save()
            print("✓ Admin user updated with password: admin123")
            
    except Exception as e:
        print(f"✗ Error creating admin: {e}")


def main():
    """Main fix function"""
    print("="*40)
    print("EGSA Application Fix Script")
    print("="*40)
    
    create_simple_admin()
    
    print("\nLogin credentials:")
    print("Username: admin")
    print("Password: admin123")
    print("\nOr use test user:")
    print("Username: testuser")
    print("Password: testpass123")
    print("="*40)


if __name__ == '__main__':
    main()
