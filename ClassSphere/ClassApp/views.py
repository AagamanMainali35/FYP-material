import datetime
import random
from django.http import  JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail,EmailMessage
from django.conf import settings
from .models import *
from .models import  profile,Event,Grade,Notification,PaymentStructure,FeePayment,Exam,Questions,Choice,StudentAnswers
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializer import Eventserializer,NotificationSerilizer
from django.contrib.auth import update_session_auth_hash 


def LandingPage(request):
    if request.user.is_authenticated:
        return render(request, 'landingpage.html')
    else:
        return redirect('login')

def RegisterPage(request):

    gradeoptions=Grade.objects.all()
    context={'grade':gradeoptions}
    if request.user.is_authenticated:
        return redirect('homepage')
    else:
        if request.method == 'POST':
            if 'signup' in request.POST:
                roleuser= request.POST.get('role')
                grade_id= request.POST.get('Grade')
                grade=Grade.objects.get(id=grade_id)
                email = request.POST.get('remail')
                password2 = request.POST.get('rpassword2')
                password = request.POST.get('rpassword')
                paymentstructure = PaymentStructure.objects.get(grade=grade)
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
                            user_profile = profile.objects.create(newprofile=newuser,role=roleuser,grade=grade,payment_structure=paymentstructure)
                            return redirect('login')
                    else:
                        messages.error(request, "Passwords do not match.")
            elif 'back' in request.POST:
                return redirect('login')
    return render(request, 'Register.html',context)

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
                    print(otp)
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
                            return redirect('ottp') 
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

def make_payment(request):
    if request.method == 'POST':
        amount_paid = request.POST.get('amount_paid')
        userprofile = request.user.profile
        payment = FeePayment(
            student=userprofile,
            amount_paid=int(amount_paid),
        )
        payment.save() 
    current_user = request.user
    try:
        userprofile = profile.objects.get(newprofile=current_user)
    except profile.DoesNotExist:
        return Response({"error": "Profile not found."}, status=404)
    fee = FeePayment.objects.filter(student=userprofile).first()
    # If fee records exist, calculate the total fee left, else set it to 0
    total_paid = 0
    if fee:
        total_paid = sum(payment.amount_paid for payment in userprofile.fee_payments.all())
        total_fee_left = userprofile.payment_structure.Totalfeeamount - total_paid
    else:
        total_fee_left = userprofile.payment_structure.Totalfeeamount  # Assuming no payments made yet
    context = {
        'userprofile': userprofile,
        'amount_paid': total_paid,
        'total_fee_left': total_fee_left,
    }
    return render(request, 'Payment', context)

def eventdetail(request,id):
    event=Event.objects.get(id=id)
    event_obj={'obj':event}
    return render(request,'eventdetail.html',context=event_obj)

@api_view(['POST'])
def send_Notification(request):
    data=NotificationSerilizer(data=request.data)
    if data.is_valid():
        users=profile.objects.all()
        print(users)
        for user in users:
            print(user)
            message=data.validated_data['NotificationMsg']
            Notification.objects.create(NotificationMsg=message,user_instance=user)
        return JsonResponse({'Status':'Message sent Sucessfully'})
    else:
        return JsonResponse({'Status':data.errors})

@login_required
def profilepage(request):
    user = request.user
    grade_list = Grade.objects.all()
    userprofile_instance = profile.objects.get(newprofile=user)

    if request.method == 'POST':
        # Handle Saving Basic Details
        if 'Savedetails' in request.POST:
            fname = request.POST.get('fname', '').strip()
            lname = request.POST.get('lname', '').strip()
            username = request.POST.get('username', '').strip()

            updated = False
            if fname:
                user.first_name = fname
                updated = True
            if lname:
                user.last_name = lname
                updated = True
            if username:
                user.username = username
                updated = True

            if updated:
                user.save()
                messages.success(request, 'Details Updated Successfully')
                return redirect('userprofile')

        # Handle Email Change
        elif 'SubmitEmailChnage' in request.POST:
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            check = authenticate(request, username=user.username, password=password)
            if check:
                user.email = email
                user.save()
                messages.success(request, 'Email Updated Successfully')
                return redirect('userprofile')
            else:
                messages.error(request, 'Wrong Credential Entered')

        elif 'passwordchange' in request.POST:
            oldpass = request.POST.get('old')
            newpass = request.POST.get('new')
            check = authenticate(request, username=user.username, password=oldpass)
            if check:
                if user.check_password(oldpass):
                    has_letter = False
                    has_digit = False
                    has_special = False
                    special_characters = "!@#$%^&*(),.?\":{}|<>"

                    for char in newpass:
                        if char.isalpha():
                            has_letter = True
                        elif char.isdigit():
                            has_digit = True
                        elif char in special_characters:
                            has_special = True

                    if len(newpass) < 8:
                        messages.error(request, 'Password must be at least 8 characters long.')
                    elif not has_letter:
                        messages.error(request, 'Password must contain at least one letter.')
                    elif not has_digit:
                        messages.error(request, 'Password must contain at least one number.')
                    elif not has_special:
                        messages.error(request, 'Password must include at least one special character.')
                    elif user.check_password(newpass):
                        messages.error(request, 'The password has been used previously.')
                    else:
                        user.set_password(newpass)
                        user.save()
                        update_session_auth_hash(request, user)
                        messages.success(request, 'Password updated successfully.')
                        return redirect('userprofile')

                else:
                    messages.error(request, 'Wrong Old Password Entered.')
            else:
                messages.error(request, 'Wrong Old Password Entered.')

        elif 'Profilepic' in request.FILES:
                profilepicture = request.FILES['Profilepic']
                profile_ins=profile.objects.get(newprofile=request.user)
                profile_ins.profile_picture=profilepicture
                profile_ins.save()
                return redirect('userprofile')
    context = {
        'Grades': grade_list,
        'user_info': {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        },
        'profile_info': {
            'picture':userprofile_instance.profile_picture,
            'grade': userprofile_instance.grade.classname
        }
    }
    return render(request, 'Userprofile.html', context)


def exam(request,id):
    questions_list = Questions.objects.filter(Exam_Instace=id) 
    question_data = [] 
    for question in questions_list:
        choices = Choice.objects.filter(question_id=question.id)  
        question_data.append({
            'question': question,  
            'choices': choices  
        })
    context = {'question_data': question_data}
    user=request.user
    check = StudentLeaderBoard.objects.filter(student_id=user, exam_id=id).exists()
    if check :
        messages.error(request,'Exam Already Taken')
        return redirect('schedule')
    else:
        if request.method=='POST':
            answers = {}
            marks=0
            Total_quest_Answered=0
            Total_Incorrect_ans=0
            Total_Correct_Answers=0
            current_exam=None
            currentuser=request.user
            for key, value in request.POST.items():
                if key.startswith('question_'):
                    key=key.replace('question_','')
                    answers.update({key: value})  

            for key,value in answers.items():
                totalquestion=Questions.objects.filter(Exam_Instace=question.Exam_Instace.id).count()
                question=Questions.objects.get(id=key)
                choice=Choice.objects.get(id=value)
                print(f'the question is {question.Question_Name} and students answers is \n {choice.choice_name}')
                Total_quest_Answered+=1
                if question.correct_answer==choice.choice_name:
                    marks+=int(question.Question_Marks)
                    Total_Correct_Answers+=1
                    exam_id=question.Exam_Instace.id
                else:
                    Total_Incorrect_ans+=1
                    print(f'invalid answer for {question.Question_Name}')
            current_exam=Exam.objects.get(id=exam_id)
            StudentLeaderBoard.objects.create(exam_id=current_exam,student_id=currentuser, Total_Question=totalquestion ,total_marks=marks,Correct=Total_Correct_Answers,Answered=Total_quest_Answered,Incorrect=Total_Incorrect_ans)
    return render(request, 'examquest.html', context)   

import hmac
import hashlib
def genSha256(key, message):
    key = key.encode('utf-8')
    message = message.encode('utf-8')
    hmac_sha256 = hmac.new(key, message, hashlib.sha256)
    return hmac_sha256.hexdigest() 

def esewa(request):
    import uuid
    ids=uuid.uuid4()
    amunt=100
    tax=20
    servicec=0
    total=amunt+tax+servicec
    secret_key='8gBm/:&EnhH.1/q'
    message=f"EPAYTEST,{amunt},{ids}"
    result=genSha256(secret_key,message)
    print(result)
    context={
        "total":total,
        "tax":tax,
        "service":servicec,
        "amount":amunt,
        "id":ids,
        "signature":result
    }
    return render(request,'test.html',context)

def leader_board(request):
    leaderboard=StudentLeaderBoard.objects.all().order_by('-total_marks')
    context={   
        "context":leaderboard
    } 
    return render(request,'Leaderboard.html',context)

def schedule(request):
    exam=Exam.objects.all()
    context={'exam':exam}
    return render(request,'exam.html',context)
