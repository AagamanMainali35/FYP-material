from django.contrib import admin
from django.urls import path,include 
from ClassApp import views

urlpatterns = [
path('all/',views.getevents,name='allevents'),
path('create/',views.create_event,name='createvents'),
path('delete/<int:id>/',views.delete,name='deleteevent'),
path('event/<int:id>/',views.geteventbyid,name='eventbyid'),
path('filter/',views.filterevents,name='filter'),
path('tag/',views.filterontag,name='filterbytag'),
path('update_event/<int:id>/',views.update_events,name='eventupdate')
]