from django.contrib import admin
from .models import  profile,Event,Grade,Notification,PaymentStructure,FeePayment,Exam,Questions,Choice,StudentLeaderBoard,attendance,Holiday

@admin.register(profile)
class profile(admin.ModelAdmin):
    list_display = ('newprofile__id','newprofile__email','role','grade')  
admin.site.register(Notification)
admin.site.register(Event)
admin.site.register(Grade)
admin.site.register(PaymentStructure)
admin.site.register(FeePayment)
admin.site.register(Exam)
admin.site.register(Questions)
admin.site.register(Choice)
admin.site.register(StudentLeaderBoard)
admin.site.register(attendance)
admin.site.register(Holiday)

