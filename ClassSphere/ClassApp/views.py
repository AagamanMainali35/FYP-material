import datetime
import random
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail,EmailMessage
from django.conf import settings
from .models import User, profile, Event
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializer import Eventserializer
from django.core.paginator import Paginator

def LandingPage(request):
    if request.user.is_authenticated:
        return render(request, 'landingpage.html')
    else:
        return redirect('login')

def RegisterPage(request):
    if request.user.is_authenticated:
        return redirect('homepage')
    else:
        if request.method == 'POST':
            if 'signup' in request.POST:
                role = request.POST.get('role')
                grade = request.POST.get('Grade')
                email = request.POST.get('remail')
                password2 = request.POST.get('rpassword2')
                password = request.POST.get('rpassword')
                char = "!@#$%^&*()-_=+[]{};:'\",.<>?/\\|`~"
                if len(password) < 10:
                    messages.error(request, "Use a stronger password")
                else:
                    contains = False
                    for i in password:
                        if i in char:
                            contains = True
                            break
                    if not contains:
                        messages.error(request, "Use a stronger password")
                    elif password == password2:
                        emailcheck = User.objects.filter(email=email).exists()
                        if emailcheck:
                            messages.error(request, "Email already exists, use a different one.")
                        else:
                            if "@" in email:
                                username = email.split("@")[0]
                            newuser = User.objects.create_user(username=username, email=email, password=password)
                            user_profile = profile.objects.create(newprofile=newuser, role=role, grade=grade)
                            return redirect('login')
                    else:
                        messages.error(request, "Passwords do not match.")
            elif 'back' in request.POST:
                return redirect('login')
    return render(request, 'Register.html')

def loginPage(request):
    if request.user.is_authenticated:
        return redirect('homepage')
    else:
        if request.method == 'POST':
            email = request.POST.get('loginemail')
            password = request.POST.get('loginpassword')
            remember = request.POST.get('rememberme')
            print(f"Remember Me value: {remember}")
            if remember:  
                request.session.set_expiry(7 * 24 * 60 * 60)  
                print("Expiry set to 7 days.")
            else:
                request.session.set_expiry(settings.SESSION_COOKIE_AGE)
                print("Expiry set to default:", settings.SESSION_COOKIE_AGE)
            try:
                userobj = User.objects.get(email=email)
                check = authenticate(request, username=userobj.username, password=password)
                if check is not None:
                    otp = random.randint(100000, 999999)
                    request.session['ottp'] = otp  
                    request.session['email'] = email  
                    request.session['isloggedin?']=True
                    request.session['workflow']='login'
                    subject = "OTP for your ClassSphere Login"
                    message = f"Dear User, {otp} is your OTP for ClassSphere. For security reasons, do not share it with others. Best regards, ClassSphere."
                    from_email = settings.EMAIL_HOST_USER
                    recipient_list = [email]
                    try:
                            send_mail(subject, message, from_email, recipient_list)
                            messages.success(request, "OTP has been sent to your email!")
                            return redirect('ottp') 
                    except Exception as e:
                            print(f"Error sending email: {e}")
                            messages.error(request, "Error sending OTP. Please try again.")
                else:
                        messages.error(request, "Invalid Username or Password.")
            except User.DoesNotExist:
                    messages.error(request, "Invalid Username or Password.")
    return render(request, 'Login.html')

def ottp(request):
    if not request.session.get('isloggedin?',False):
        return redirect('homepage')
    else:
        if request.method == 'POST':
            if request.session.get('workflow')=='login':
                entered_otp = request.POST.get('ottp') 
                email = request.session.get('email')  
                stored_otp = request.session.get('ottp') 
                if stored_otp is None or email is None:
                    messages.error(request, "Session has expired. Please log in again.")
                    return redirect('login') 
                if str(entered_otp) == str(stored_otp):
                    userobj = User.objects.get(email=email)
                    login(request, userobj)
                    del request.session['ottp']  
                    del request.session['email'] 
                    del request.session['isloggedin?']
                    del request.session['workflow']
                    messages.success(request, "Validation successfull")
                    return redirect('homepage') 
                else:
                    messages.error(request, "Invalid OTP. Please try again.")   
            elif request.session.get('workflow') =='Forgetpassword':
                if request.method=='POST':
                     entered_otp=request.POST.get('ottp')
                     stored_otp=request.session.get('ottp')
                     print(entered_otp)
                     print(stored_otp)
                     return redirect('reset')
                return redirect('forgetpass')
    return render(request, 'otp.html')
   
def logouted(request):
    logout(request)
    return redirect('login')

def forgetpass(request):
    # if not request.session.get('isloggedin?',False):
    #     return redirect('homepage')
    # else:
        if request.method=='POST':
            email=request.POST.get('forgotemail')
            request.session['workflow']='Forgetpassword'
            otp = random.randint(100000, 999999)
            request.session['ottp'] = otp  
            request.session['email'] = email 
            request.session['isloggedin?']=True
            subject = "OTP for your ClassSphere Login"
            message = f"Dear User, {otp} is your OTP for ClassSphere password Reset . For security reasons, do not share it with others. Best regards, ClassSphere."
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]
            try:
                    send_mail(subject, message, from_email, recipient_list)
                    messages.success(request, "OTP has been sent to your email!")
                    return redirect('ottp') 
            except Exception as e:
                    print(f"Error sending email: {e}")
                    messages.error(request, "Error sending OTP. Please try again.")
            return redirect('ottp')
        return render(request,'ForgotPassword.html')

def reset(request):
    if not request.session.get('isloggedin?',False):
        return redirect('homepage')
    else:
        if request.method == 'POST':  
            password2 = request.POST.get('rpassword2')
            password = request.POST.get('rpassword')
            if password is None or password2 is None:
                messages.error(request, "Please enter both password fields.")
                return render(request, 'passwordreset.html')
            char = "!@#$%^&*()-_=+[]{};:'\",.<>?/\\|`~"
            if len(password) < 10:
                messages.error(request, "Use a stronger password.")
            else:
                contains = False
                for i in password:
                    if i in char:
                        contains = True
                        break
                if not contains:
                    messages.error(request, "Use a stronger password.")
                elif password == password2:
                    email = request.session.get('email')
                    if email:
                        try:
                            userobj = User.objects.get(email=email) 
                            userobj.set_password(password)  
                            userobj.save()  
                            messages.success(request, "Password successfully updated.")
                            return redirect('login')
                        except User.DoesNotExist:
                            messages.error(request, "User not found.")
                    else:
                        messages.error(request, "Session has expired. Please log in again.")
        return render(request, 'passwordreset.html')

def event(request):
    return render(request,'event.html')

@api_view(['POST'])
def contact(request):
    postdata = request.data
    if postdata:
        file=request.FILES.get('file')
        message = f"<b>From:</b> {postdata['email']} <br><b>Message:</b> <br>{postdata.get('message')}"
        subject = postdata.get('subject')
        email_message = EmailMessage(subject=subject,body=message,to=[settings.EMAIL_HOST_USER])
        email_message.content_subtype = "html"
        if file:
            email_message.attach(file.name, file.read(), file.content_type)
        try:
            email_message.send()
            response_data = {
                "status": "mail sent successfully"
            }
        except:
            response_data = {
                "status": "mail not sent"
            }
        return JsonResponse(response_data, status=200)

# Apis for all event relates operations
@api_view(['GET'])
def getevents(request):
 events=Event.objects.all()
 serializer=Eventserializer(events,many=True)
 return JsonResponse(serializer.data,safe=False)

@api_view(['POST'])
def create_event(request):
    potsdata=request.data
    serializer=Eventserializer(data=potsdata)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response({" Status ":serializer.errors})

@api_view(['DELETE'])
def delete(request,id):
    event=get_object_or_404(Event,pk=id)
    try:
        event.delete()
    except: 
        return Response('Event not found')
    return Response('Event deleted successfully')

@api_view(['DELETE'])
def deleteall(request):
    data=Event.objects.all()
    for i in data:
        i.delete()
    return JsonResponse({"Status":"Events Deleted Sucessfully"})

@api_view(['GET'])
def geteventbyid(request,id):
    event=Event.objects.get(id=id)
    serializer=Eventserializer(event)
    return JsonResponse(serializer.data)


@api_view(['POST'])
def filterevents(request):
    title = request.data.get('title', None)
    paidstatus = request.data.get('paidstatus', None)
    time_filter = request.data.get('timeFilter', None)
    events = Event.objects.all() 
    if title:
        events = events.filter(title__icontains=title)
    if paidstatus:
        if paidstatus == "paid":
            events = events.filter(is_paid=True)
        elif paidstatus == "unpaid":
            events = events.filter(is_paid=False)
    if time_filter:
        if time_filter == 'week':
            start_of_week = datetime.datetime.now() - datetime.timedelta(days=datetime.datetime.now().weekday())
            events = events.filter(date__gte=start_of_week)
        elif time_filter == 'month':
            start_of_month = datetime.datetime.now().replace(day=1)
            events = events.filter(date__gte=start_of_month)
    event_data=Eventserializer(events,many=True)
    return JsonResponse({'events': event_data.data})

def eventdetail(request,id):
    event=Event.objects.get(id=id)
    event_obj={'obj':event}
    return render(request,'eventdetail.html',context=event_obj)