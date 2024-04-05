from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('flat/', views.flat, name='flat'),
    path('house/', views.house, name='house'),
    path('house-submit/', views.house_submit, name='house-submit'),
    path('flat-submit/', views.flat_submit, name='flat-submit'),
]