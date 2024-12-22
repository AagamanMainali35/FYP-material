import random
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import User, profile

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
            print(f"Current session: {request.session.get('workflow')}")
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
