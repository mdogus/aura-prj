from django.urls import path

from .views import (
    AdvisorDashboardView,
    CoordinatorDashboardView,
    DashboardHomeRedirectView,
    StudentDashboardView,
    VolunteerDashboardView,
)

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardHomeRedirectView.as_view(), name='home'),
    path('student/', StudentDashboardView.as_view(), name='student'),
    path('volunteer/', VolunteerDashboardView.as_view(), name='volunteer'),
    path('advisor/', AdvisorDashboardView.as_view(), name='advisor'),
    path('coordinator/', CoordinatorDashboardView.as_view(), name='coordinator'),
]
