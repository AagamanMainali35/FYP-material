from django.contrib import admin
from django.urls import path,include 
from ClassApp import views
urlpatterns = [
path('all/',views.getallExam,name='allevents'),
path('update/',views.updateexam,name='update'),
path('delete/<int:id>/',views.deleteExam,name='delete')
]