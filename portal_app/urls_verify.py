from django.urls import path
from .views_verify import verify_certificate

urlpatterns = [
    path('verify-certificate/', verify_certificate, name='verify_certificate'),
]
