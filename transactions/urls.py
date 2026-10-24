from django.urls import path
from . import views
urlpatterns = [
    path('add/', views.add_transaction, name='add_transaction'),
    path('', views.transaction_list, name='transaction_list'),
    path('<int:pk>/edit/', views.edit_transaction, name='edit_transaction'),
    path('<int:pk>/delete/', views.delete_transaction, name='delete_transaction'),
    path('export/csv/',views.export_transactions_csv,name='export_transactions_csv'),
]