from django.contrib import admin
from django.urls import path,include 
from ClassApp import views

urlpatterns = [
path('allevents/',views.getevents,name='allevents'),
path('createvent/',views.create_event,name='createvents'),
path('deleteevent/<int:id>/',views.delete,name='deleteevent'),
path('event/<int:id>/',views.geteventbyid,name='eventbyid'),
]