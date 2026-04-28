from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # User dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_file, name='upload'),
    path('summarize/', views.summarize_view, name='summarize'),
    path('history/', views.history_view, name='history'),
    path('profile/', views.profile_view, name='profile'),

    # User: delete history & account
    path('history/<str:item_id>/delete/', views.delete_history_item_view, name='delete_history_item'),
    path('history/clear/', views.clear_history_view, name='clear_history'),
    path('account/delete/', views.delete_account_view, name='delete_account'),
    path('account-deleted/', views.account_deleted_view, name='account_deleted'),

    # Admin dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/activity/', views.admin_activity, name='admin_activity'),
    path('admin/audit-logs/', views.admin_audit_logs, name='admin_audit_logs'),
    path('admin/users/<str:user_id>/toggle/', views.admin_toggle_user, name='admin_toggle_user'),
    path('admin/users/<str:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),

    # Audio / Video summarize
    path('audio-summarize/', views.audio_summarize_view, name='audio_summarize'),
    path('video-summarize/', views.video_summarize_view, name='video_summarize'),

    # API
    path('api/history/', views.api_history, name='api_history'),
]
