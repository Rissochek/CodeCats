from django.urls import path
from . import views

urlpatterns = [
    path('save-articles/', views.save_articles, name='save_articles'),
]