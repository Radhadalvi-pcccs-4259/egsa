from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class UtilityReading(models.Model):
    """Model for storing utility readings"""
    UTILITY_TYPES = [
        ('electricity', 'Electricity'),
        ('gas', 'Gas'),
        ('steam', 'Steam'),
        ('air_conditioning', 'Air Conditioning'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    utility_type = models.CharField(max_length=20, choices=UTILITY_TYPES)
    reading_value = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, default='kWh')
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reading_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, default='Main Building')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-reading_date']
        
    def __str__(self):
        return f"{self.utility_type} - {self.reading_value} {self.unit}"

class UserProfile(models.Model):
    """Extended user profile for additional information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    department = models.CharField(max_length=100, blank=True)
    notification_preferences = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} Profile" if self.user else "User Profile"

class UtilityReport(models.Model):
    """Model for storing generated reports"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    report_name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50)
    date_generated = models.DateTimeField(auto_now_add=True)
    s3_file_key = models.CharField(max_length=500, blank=True)  # For AWS S3 storage
    
    def __str__(self):
        return f"{self.report_name}"
