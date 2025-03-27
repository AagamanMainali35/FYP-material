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
    path('pay/',views.make_payment),
    path('send/',views.send_Notification),
    path('profile/',views.profilepage,name='userprofile')
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
