from django.urls import path
from . import views

urlpatterns = [
    path('detail/', views.account_detail_view, name='account_detail'),
    path('detail/<int:account_no>/', views.account_detail_view, name='account_detail'),
    path('create/', views.create_account_view, name='create_account'),
    path('lookup/', views.account_lookup_view, name='account_lookup'),
    path('list/', views.admin_accounts_view, name='admin_accounts'),
] 