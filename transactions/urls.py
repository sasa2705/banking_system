from django.urls import path
from . import views

urlpatterns = [
    path('deposit/', views.deposit_view, name='deposit'),
    path('withdraw/', views.withdrawal_view, name='withdraw'),
    path('transfer/', views.transfer_view, name='transfer'),
    path('history/', views.transaction_history_view, name='transaction_history'),
    path('admin-transactions/', views.admin_transactions_view, name='admin_transactions'),
    path('create/', views.create_transaction_view, name='create_transaction'),
    path('detail/<int:transaction_id>/', views.transaction_detail_view, name='transaction_detail'),
    path('approve/<int:transaction_id>/', views.approve_transaction_view, name='approve_transaction'),
    path('reject/<int:transaction_id>/', views.reject_transaction_view, name='reject_transaction'),
] 