from django.urls import path

from .views import LibraryDetailView, LibraryDownloadView, LibraryListView

app_name = 'library'

urlpatterns = [
    path('', LibraryListView.as_view(), name='list'),
    path('<int:pk>/', LibraryDetailView.as_view(), name='detail'),
    path('<int:pk>/download/', LibraryDownloadView.as_view(), name='download'),
]
