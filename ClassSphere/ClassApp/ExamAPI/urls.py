from django.contrib import admin
from django.urls import path,include 
from ClassApp import views
urlpatterns = [
path('all/',views.getallExam,name='allevents'),
]