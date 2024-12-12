import random
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import User, profile

# Landing page view
def LandingPage(request):
    if request.user.is_authenticated:
        return render(request, 'landingpage.html')
    else:
        return redirect('login')

# Login page view
def loginPage(request):
    if request.method == 'POST':
        print('now checking the buttons ')
        if 'signup' in request.POST:
            role = request.POST.get('role')
            grade = request.POST.get('Grade')
            email = request.POST.get('remail')
            password2 = request.POST.get('rpassword2')
            password = request.POST.get('rpassword')
            char = "!@#$%^&*()-_=+[]{};:'\",.<>?/\\|`~"

            # Password validation
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
                        newuser = User.objects.create(username=username, email=email, password=password)
                        user_profile = profile.objects.create(newprofile=newuser, role=role, grade=grade)
                        messages.success(request, "Account created successfully.")
                else:
                    messages.error(request, "Passwords do not match.")

        elif 'signin' in request.POST:
            print('This is post method:')
            email = request.POST.get('loginemail')
            password = request.POST.get('loginpassword')
            print(email, password)
            try:
                userobj = User.objects.get(email=email)
                check = authenticate(request, username=userobj.username, password=password)
                if check is not None:
                    otp = random.randint(100000, 999999)
                    request.session['ottp'] = otp  
                    request.session['email'] = email  
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
    if request.method == 'POST':
        entered_otp = request.POST.get('ottp') 
        email = request.session.get('email')  
        stored_otp = request.session.get('ottp') 
        print(stored_otp)

        if stored_otp is None or email is None:
            messages.error(request, "Session has expired. Please log in again.")
            return redirect('login') 

        if str(entered_otp) == str(stored_otp):
            userobj = User.objects.get(email=email)
            login(request, userobj)
            del request.session['ottp']  
            del request.session['email'] 
            messages.success(request, "Logged in successfully!")
            return redirect('homepage')  
        else:
            messages.error(request, "Invalid OTP. Please try again.")
    return render(request, 'otp.html') 


def logouted(request):
    logout(request)
    return redirect('login')
