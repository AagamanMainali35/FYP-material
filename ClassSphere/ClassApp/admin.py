from django.contrib import admin
from .models import  profile,Event

@admin.register(profile)
class profile(admin.ModelAdmin):
    list_display = ('newprofile__id','newprofile__email','role','grade')  

admin.site.register(Event)

