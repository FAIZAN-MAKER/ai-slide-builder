from django.urls import path
from . import views

urlpatterns = [
    path('', views.slide_builder, name='slide_builder'),
    path('api/generate_slides/', views.generate_slides, name='generate_slides'),
]