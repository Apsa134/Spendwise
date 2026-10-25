from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('monthly-report/',views.send_monthly_report,name='send_monthly_report',),
]