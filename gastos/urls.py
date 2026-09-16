from django.urls import path
from .views import dashboard, whatsapp_webhook

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("api/whatsapp/webhook/", whatsapp_webhook, name="whatsapp_webhook"),
]
