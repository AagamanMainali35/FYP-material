from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from ClassApp import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.LandingPage,name='homepage'),
    path('login/',views.loginPage,name='login'),
    path('register/',views.RegisterPage,name='register'),
    path('logout/',views.logouted,name='logout'),
    path('ottp/',views.ottp,name="ottp"),
    path('forget/',views.forgetpass,name='forgetpass'),
    path('reset/',views.reset,name='reset'),
    path('contact/',views.contact,name='contact'),
    path('event/',views.event,name='eventpage'),
    path('detail/<int:id>/',views.eventdetail,name='DetailPage'),
    path('events/',include('ClassApp.api.urls')),
    path('pay/',views.make_payment,name='pay'),
    path('send/',views.send_Notification),
    path('profile/',views.profilepage,name='userprofile'),
    path('schedule/',views.schedule,name='schedule'),
    path('exam/<int:id>/',views.exam,name="exam"),
    path('leaderboard/',views.leader_board,name='leaderboard'),
    path('attendance/',views.attendance_view,name='attendance'),
    path('upload-data/',views.get_attendance_data,name='uplaoddata'),
    path('get_filter/',views.get_filter,name='getfilter'),
    path('get_data/',views.printPDF,name='pdf'),
    path('holiday/',views.holiday,name='holiday'),
    path('create/',views.Exam_create,name='createExam'),
    path('handle/',views.handlecreate,name='handledata'),
    path('user/Notification/',views.Notification,name='Notification'),
    path('admin2/',views.adminpage)
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
