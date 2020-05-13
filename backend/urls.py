from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('annotate/<str:project>', views.annotate, name='annotate'),
    path('submit/<str:project>', views.submit_annotations, name='submit_annotations')
]
