from django.urls import path

from .views import (
    CoordinatorUserDetailView,
    CoordinatorUserListView,
    CoordinatorUserToggleActiveView,
    ProfileOnboardingView,
    SignUpView,
)

app_name = 'users'

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('profile/', ProfileOnboardingView.as_view(), name='profile_onboarding'),
    path('coordinator/users/', CoordinatorUserListView.as_view(), name='coordinator_user_list'),
    path(
        'coordinator/users/<int:pk>/',
        CoordinatorUserDetailView.as_view(),
        name='coordinator_user_detail',
    ),
    path(
        'coordinator/users/<int:pk>/toggle-active/',
        CoordinatorUserToggleActiveView.as_view(),
        name='coordinator_user_toggle_active',
    ),
]
