from django.contrib import admin
from .models import  profile

@admin.register(profile)
class profile(admin.ModelAdmin):
    list_display = ('newprofile__id','newprofile__email','role','grade')  

