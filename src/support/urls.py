from django.urls import path

from .views import (
    CoordinatorAssignVolunteerView,
    CoordinatorInterventionNoteCreateView,
    CoordinatorRequestPriorityUpdateView,
    CoordinatorRequestDetailView,
    CoordinatorRequestListView,
    CoordinatorRequestStatusUpdateView,
    StudentRequestCreateView,
    StudentRequestDetailView,
    StudentRequestListView,
    StudentRequestMaterialCreateView,
    StudentRequestMessageCreateView,
    StudentRequestStatusUpdateView,
    VolunteerActiveSupportListView,
    VolunteerClaimRequestView,
    VolunteerOpenRequestListView,
    VolunteerRequestDetailView,
    VolunteerRequestMaterialCreateView,
    VolunteerRequestMessageCreateView,
    VolunteerRequestStatusUpdateView,
)

app_name = 'support'

urlpatterns = [
    path('requests/', StudentRequestListView.as_view(), name='student_request_list'),
    path('requests/new/', StudentRequestCreateView.as_view(), name='student_request_create'),
    path(
        'requests/<int:pk>/',
        StudentRequestDetailView.as_view(),
        name='student_request_detail',
    ),
    path(
        'requests/<int:pk>/status/',
        StudentRequestStatusUpdateView.as_view(),
        name='student_request_status',
    ),
    path(
        'requests/<int:pk>/messages/',
        StudentRequestMessageCreateView.as_view(),
        name='student_request_message_create',
    ),
    path(
        'requests/<int:pk>/materials/',
        StudentRequestMaterialCreateView.as_view(),
        name='student_request_material_create',
    ),
    path(
        'coordinator/requests/',
        CoordinatorRequestListView.as_view(),
        name='coordinator_request_list',
    ),
    path(
        'coordinator/requests/<int:pk>/',
        CoordinatorRequestDetailView.as_view(),
        name='coordinator_request_detail',
    ),
    path(
        'coordinator/requests/<int:pk>/assign/',
        CoordinatorAssignVolunteerView.as_view(),
        name='coordinator_request_assign',
    ),
    path(
        'coordinator/requests/<int:pk>/status/',
        CoordinatorRequestStatusUpdateView.as_view(),
        name='coordinator_request_status',
    ),
    path(
        'coordinator/requests/<int:pk>/priority/',
        CoordinatorRequestPriorityUpdateView.as_view(),
        name='coordinator_request_priority',
    ),
    path(
        'coordinator/requests/<int:pk>/notes/',
        CoordinatorInterventionNoteCreateView.as_view(),
        name='coordinator_request_note_create',
    ),
    path('volunteer/open/', VolunteerOpenRequestListView.as_view(), name='volunteer_open_request_list'),
    path('volunteer/active/', VolunteerActiveSupportListView.as_view(), name='volunteer_active_support_list'),
    path(
        'volunteer/requests/<int:pk>/',
        VolunteerRequestDetailView.as_view(),
        name='volunteer_request_detail',
    ),
    path(
        'volunteer/requests/<int:pk>/claim/',
        VolunteerClaimRequestView.as_view(),
        name='volunteer_request_claim',
    ),
    path(
        'volunteer/requests/<int:pk>/status/',
        VolunteerRequestStatusUpdateView.as_view(),
        name='volunteer_request_status',
    ),
    path(
        'volunteer/requests/<int:pk>/messages/',
        VolunteerRequestMessageCreateView.as_view(),
        name='volunteer_request_message_create',
    ),
    path(
        'volunteer/requests/<int:pk>/materials/',
        VolunteerRequestMaterialCreateView.as_view(),
        name='volunteer_request_material_create',
    ),
]
