import random
from django.shortcuts import render,redirect
from .models import User, profile
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.core.mail import send_mail
from django.conf import settings




# Create your views here.
def LandingPage(request):
    if request.user.is_authenticated:
        return render(request,'landingpage.html')
    else:return redirect('login')

def loginPage(request):
    if request.method=='POST':
        print('now checking the buttons ')
        if 'signup' in request.POST:
            role=request.POST.get('role')
            grade=request.POST.get('Grade')
            email=request.POST.get('remail')
            password2=request.POST.get('rpassword2')
            password=request.POST.get('rpassword')
            char="!@#$%^&*()-_=+[]{};:'\",.<>?/\\|`~"
            if len(password)<10:
                messages.error(request, "Use a stronger password")
            else:
                contains=False
                for i in password:
                    if i in char: 
                        contains=True
                        break
                if contains==False:
                        messages.error(request, "Use a stronger password")    
                if contains==True:       
                    if password==password2:
                        emailcheck=User.objects.filter(email=email).exists()
                        print(emailcheck)
                        if emailcheck==True:
                            messages.error(request, "Email Already exists use a diffrent one ?")
                        else:
                            if  "@" in email:
                                username= email.split("@")[0]
                            newuser=User.objects.create(username=username,email=email,password=password)
                            user_profile = profile.objects.create(newprofile=newuser, role=role, grade=grade)
                            messages.success(request, "Account Created Sucessfull..")
                    else:
                        messages.error(request, "Please enter a matching password")

        elif 'signin' in request.POST:
            print('This is post method:')
            email = request.POST.get('loginemail')
            password = request.POST.get('loginpassword')
            print(email, password)
            try:
                userobj = User.objects.get(email=email) 
                global check
                check = authenticate(request, username=userobj.username, password=password)
                print(check)
                otp=random.randint(100000, 999999)
                subject=f"OTP for you CLassSphere Login "
                message = f"Dear User {otp} is you OTP for classSphere . For security Reason sont share it with others . Best regards ClassSphere ." 
                from_email = settings.EMAIL_HOST_USER
                recipient_list = [email] 
                try:
                    send_mail(subject, message, from_email, recipient_list)
                    messages.success(request, "OTP has been sent to your email!")
                    return redirect('ottp')
                except Exception as e:
                    print(f"Error sending email: {e}")
                    messages.error(request, "Error sending OTP. Please try again.")
            except User.DoesNotExist: 
                return render(request, 'login.html', messages.error(request, "Please Check your credential"))
    return render(request,'Login.html')


def ottp(request):
    if 'otp' in request.POST:
            ottp=request.POST['otp']
            print(ottp) 
                # if check is not None:
                #     login(request, check)
                #     print('logged in')
                #     return redirect('homepage')
                # else:
                #     return render(request, 'Login.html',messages.error(request, "Please Check your credential"))
    return render(request,'ottp.html')


def logouted(request):
    logout(request)
    return redirect('login')

