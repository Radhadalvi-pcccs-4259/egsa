#!/usr/bin/env python3
"""
Generate a secure Django secret key for production deployment.
Run this script to generate a new secret key for GitHub secrets.
"""

from django.core.management.utils import get_random_secret_key

if __name__ == "__main__":
    secret_key = get_random_secret_key()
    print("=" * 60)
    print("DJANGO SECRET KEY GENERATOR")
    print("=" * 60)
    print(f"Generated Secret Key: {secret_key}")
    print("=" * 60)
    print("Copy the above secret key and add it to GitHub Secrets as:")
    print("Secret Name: DJANGO_SECRET_KEY")
    print(f"Secret Value: {secret_key}")
    print("=" * 60)
