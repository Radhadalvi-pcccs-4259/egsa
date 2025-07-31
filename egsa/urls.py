from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('utilities/', views.utility_management, name='utility_management'),
    path('utilities/edit/<uuid:reading_id>/', views.edit_reading, name='edit_reading'),
    path('utilities/delete/<uuid:reading_id>/', views.delete_reading, name='delete_reading'),
    path('reports/', views.reports, name='reports'),
    path('reports/download/<uuid:report_id>/', views.download_report, name='download_report'),
    path('profile/', views.profile, name='profile'),
    path('api/usage-data/', views.api_usage_data, name='api_usage_data'),
]
