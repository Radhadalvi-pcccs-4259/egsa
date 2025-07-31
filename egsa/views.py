from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Sum, Avg, Count
from decimal import Decimal
import json
from datetime import datetime, timedelta
import logging

from .models import UtilityReading, UserProfile, UtilityReport
from .utils.egsa_calculator import get_analyzer, UtilityCalculatorFactory
from .utils.aws_integration import AWSManagerFactory

# Set up logging
logger = logging.getLogger(__name__)


def login_view(request):
    """Login page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Log user login
            cloudwatch = AWSManagerFactory.get_cloudwatch_manager()
            cloudwatch.log_user_action(user.id, 'login')
            
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'egsa/login.html')


@login_required
def logout_view(request):
    """Logout user"""
    # Log user logout
    cloudwatch = AWSManagerFactory.get_cloudwatch_manager()
    cloudwatch.log_user_action(request.user.id, 'logout')
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def dashboard(request):
    """Main dashboard - Page 1"""
    # Get recent readings
    recent_readings = UtilityReading.objects.filter(user=request.user)[:5]
    
    # Get monthly statistics
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_stats = UtilityReading.objects.filter(
        user=request.user,
        reading_date__month=current_month,
        reading_date__year=current_year
    ).values('utility_type').annotate(
        total_usage=Sum('reading_value'),
        total_cost=Sum('cost'),
        avg_usage=Avg('reading_value'),
        reading_count=Count('id')
    )
    
    # Calculate efficiency using our custom library
    analyzer = get_analyzer()
    efficiency_data = {}
    
    for stat in monthly_stats:
        utility_type = stat['utility_type']
        calculator = UtilityCalculatorFactory.create_calculator(utility_type)
        
        # Mock benchmark data (in real app, this would come from settings)
        benchmarks = {
            'electricity': 400,
            'gas': 100,
            'steam': 50,
            'air_conditioning': 200
        }
        
        efficiency_rating = calculator.get_efficiency_rating(
            float(stat['total_usage'] or 0),
            benchmarks.get(utility_type, 100)
        )
        
        efficiency_data[utility_type] = {
            'rating': efficiency_rating,
            'usage': float(stat['total_usage'] or 0),
            'cost': float(stat['total_cost'] or 0)
        }
    
    # Send metrics to CloudWatch
    cloudwatch = AWSManagerFactory.get_cloudwatch_manager()
    for utility_type, data in efficiency_data.items():
        cloudwatch.put_custom_metric(
            f'{utility_type}_monthly_usage',
            data['usage'],
            'Count',
            utility_type
        )
    
    # Check for high usage alerts
    sns = AWSManagerFactory.get_sns_manager()
    for utility_type, data in efficiency_data.items():
        thresholds = {
            'electricity': 500,
            'gas': 150,
            'steam': 75,
            'air_conditioning': 300
        }
        
        threshold = thresholds.get(utility_type, 100)
        if data['usage'] > threshold:
            sns.send_usage_alert(utility_type, data['usage'], threshold)
    
    context = {
        'recent_readings': recent_readings,
        'monthly_stats': monthly_stats,
        'efficiency_data': efficiency_data,
        'current_month': current_month,
        'current_year': current_year
    }
    
    return render(request, 'egsa/dashboard.html', context)


@login_required
def utility_management(request):
    """Utility management page - Page 2 (CRUD operations)"""
    if request.method == 'POST':
        # Create new utility reading
        utility_type = request.POST.get('utility_type')
        reading_value = request.POST.get('reading_value')
        unit = request.POST.get('unit', 'kWh')
        notes = request.POST.get('notes', '')
        location = request.POST.get('location', 'Main Building')
        
        try:
            # Calculate cost using our custom library
            calculator = UtilityCalculatorFactory.create_calculator(utility_type)
            cost = calculator.calculate_cost(float(reading_value))
            
            # Create reading
            reading = UtilityReading.objects.create(
                user=request.user,
                utility_type=utility_type,
                reading_value=Decimal(reading_value),
                unit=unit,
                cost=cost,
                notes=notes,
                location=location
            )
            
            # Log to CloudWatch
            cloudwatch = AWSManagerFactory.get_cloudwatch_manager()
            cloudwatch.log_utility_event('reading_created', {
                'user_id': request.user.id,
                'utility_type': utility_type,
                'reading_value': float(reading_value),
                'cost': float(cost)
            })
            
            # Store in RDS for backup
            rds = AWSManagerFactory.get_rds_manager()
            rds.store_utility_reading({
                'user_id': request.user.id,
                'utility_type': utility_type,
                'reading_value': float(reading_value),
                'unit': unit,
                'cost': float(cost),
                'reading_date': reading.reading_date,
                'notes': notes,
                'location': location
            })
            
            messages.success(request, f'Utility reading added successfully! Cost: ${cost:.2f}')
            
        except Exception as e:
            messages.error(request, f'Error adding reading: {str(e)}')
            logger.error(f"Error creating utility reading: {e}")
        
        return redirect('utility_management')
    
    # Get all readings with pagination
    readings_list = UtilityReading.objects.filter(user=request.user).order_by('-reading_date')
    paginator = Paginator(readings_list, 10)  # Show 10 readings per page
    
    page_number = request.GET.get('page')
    readings = paginator.get_page(page_number)
    
    context = {
        'readings': readings,
        'utility_types': UtilityReading.UTILITY_TYPES
    }
    
    return render(request, 'egsa/utility_management.html', context)


@login_required
def edit_reading(request, reading_id):
    """Edit utility reading"""
    reading = get_object_or_404(UtilityReading, id=reading_id, user=request.user)
    
    if request.method == 'POST':
        reading.utility_type = request.POST.get('utility_type')
        reading.reading_value = Decimal(request.POST.get('reading_value'))
        reading.unit = request.POST.get('unit')
        reading.notes = request.POST.get('notes')
        reading.location = request.POST.get('location')
        
        # Recalculate cost
        calculator = UtilityCalculatorFactory.create_calculator(reading.utility_type)
        reading.cost = calculator.calculate_cost(float(reading.reading_value))
        
        reading.save()
        
        # Log update
        cloudwatch = AWSManagerFactory.get_cloudwatch_manager()
        cloudwatch.log_user_action(request.user.id, 'reading_updated', {'reading_id': str(reading_id)})
        
        messages.success(request, 'Reading updated successfully!')
        return redirect('utility_management')
    
    context = {
        'reading': reading,
        'utility_types': UtilityReading.UTILITY_TYPES
    }
    
    return render(request, 'egsa/edit_reading.html', context)


@login_required
def delete_reading(request, reading_id):
    """Delete utility reading"""
    reading = get_object_or_404(UtilityReading, id=reading_id, user=request.user)
    
    if request.method == 'POST':
        # Log deletion
        cloudwatch = AWSManagerFactory.get_cloudwatch_manager()
        cloudwatch.log_user_action(request.user.id, 'reading_deleted', {'reading_id': str(reading_id)})
        
        reading.delete()
        messages.success(request, 'Reading deleted successfully!')
        return redirect('utility_management')
    
    context = {'reading': reading}
    return render(request, 'egsa/confirm_delete.html', context)


@login_required
def reports(request):
    """Reports page - Page 3"""
    # Generate monthly report
    month = int(request.GET.get('month', datetime.now().month))
    year = int(request.GET.get('year', datetime.now().year))
    
    # Get readings for the month
    readings = UtilityReading.objects.filter(
        user=request.user,
        reading_date__month=month,
        reading_date__year=year
    )
    
    # Aggregate data by utility type
    utility_data = {}
    for reading in readings:
        utility_type = reading.utility_type
        if utility_type not in utility_data:
            utility_data[utility_type] = {
                'usage': 0,
                'benchmark': 100  # Default benchmark
            }
        utility_data[utility_type]['usage'] += float(reading.reading_value)
    
    # Use our custom analyzer
    analyzer = get_analyzer()
    analysis = analyzer.comprehensive_analysis(utility_data)
    
    # Generate report content
    report_content = f"""
    EGSA Monthly Report - {year}-{month:02d}
    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    User: {request.user.get_full_name() or request.user.username}
    
    SUMMARY:
    Total Cost: ${float(analysis['total_cost']):.2f}
    
    EFFICIENCY SCORES:
    """
    
    for utility, score in analysis['efficiency_scores'].items():
        report_content += f"    {utility.title()}: {score}\n"
    
    report_content += f"\n    RECOMMENDATIONS:\n"
    for rec in analysis['recommendations']:
        report_content += f"    - {rec}\n"
    
    # Store report in S3
    s3 = AWSManagerFactory.get_s3_manager()
    file_key = f"user_{request.user.id}_report_{year}_{month:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    if s3.upload_report(report_content, file_key):
        # Create report record
        report = UtilityReport.objects.create(
            user=request.user,
            report_name=f"Monthly Report {year}-{month:02d}",
            report_type="monthly",
            s3_file_key=file_key
        )
        
        # Send email notification
        ses = AWSManagerFactory.get_ses_manager()
        if request.user.email:
            ses.send_monthly_report_email(request.user.email, {
                'period': f"{year}-{month:02d}",
                'total_cost': float(analysis['total_cost']),
                'average_efficiency': analysis['efficiency_scores'],
                'cost_trend': 'Current Month'
            })
    
    # Get previous reports
    previous_reports = UtilityReport.objects.filter(user=request.user).order_by('-date_generated')[:10]
    
    context = {
        'analysis': analysis,
        'month': month,
        'year': year,
        'report_content': report_content,
        'previous_reports': previous_reports,
        'readings_count': readings.count()
    }
    
    return render(request, 'egsa/reports.html', context)


@login_required
def download_report(request, report_id):
    """Download report from S3"""
    report = get_object_or_404(UtilityReport, id=report_id, user=request.user)
    
    s3 = AWSManagerFactory.get_s3_manager()
    content = s3.download_report(report.s3_file_key)
    
    if content:
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{report.report_name}.txt"'
        return response
    else:
        messages.error(request, 'Report not found or error downloading from S3.')
        return redirect('reports')


@login_required
def profile(request):
    """User profile page - Page 4"""
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update user information
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        # Update profile
        profile.phone = request.POST.get('phone', '')
        profile.department = request.POST.get('department', '')
        profile.notification_preferences = request.POST.get('notifications') == 'on'
        profile.save()
        
        # Log profile update
        cloudwatch = AWSManagerFactory.get_cloudwatch_manager()
        cloudwatch.log_user_action(request.user.id, 'profile_updated')
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    # Get user statistics
    total_readings = UtilityReading.objects.filter(user=request.user).count()
    total_cost = UtilityReading.objects.filter(user=request.user).aggregate(
        total=Sum('cost')
    )['total'] or Decimal('0')
    
    # Get recent activity
    recent_readings = UtilityReading.objects.filter(user=request.user)[:5]
    
    context = {
        'profile': profile,
        'total_readings': total_readings,
        'total_cost': total_cost,
        'recent_readings': recent_readings
    }
    
    return render(request, 'egsa/profile.html', context)


@csrf_exempt
@login_required
def api_usage_data(request):
    """API endpoint for usage data (for charts)"""
    if request.method == 'GET':
        utility_type = request.GET.get('type', 'electricity')
        
        # Get last 12 months of data
        readings = UtilityReading.objects.filter(
            user=request.user,
            utility_type=utility_type,
            reading_date__gte=datetime.now() - timedelta(days=365)
        ).order_by('reading_date')
        
        data = []
        for reading in readings:
            data.append({
                'date': reading.reading_date.strftime('%Y-%m-%d'),
                'value': float(reading.reading_value),
                'cost': float(reading.cost or 0)
            })
        
        return JsonResponse({'data': data})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
