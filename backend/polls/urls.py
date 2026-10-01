from django.urls import path
from . import views

app_name = 'polls'

urlpatterns = [
    path('', views.feed_view, name='feed'),
    path('poll/<int:poll_id>/', views.poll_detail_view, name='poll_detail'),
    path('create/', views.poll_create_view, name='poll_create'),
    path('api/poll/<int:poll_id>/vote/', views.vote_api, name='vote_api'),
    path('api/poll/<int:poll_id>/bookmark/', views.bookmark_api, name='bookmark_api'),
    path('poll/<int:poll_id>/toggle-active/', views.poll_toggle_active, name='poll_toggle_active'),
    path('poll/<int:poll_id>/delete/', views.poll_delete, name='poll_delete'),
]
