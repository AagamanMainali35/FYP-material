import datetime
import random
import uuid
import requests
import json
from django.http import  JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail,EmailMessage
from django.conf import settings
from .models import  profile,Event,Grade,Notification as notifications,PaymentStructure,FeePayment,Exam,Questions,Choice,StudentAnswers,attendance,User,StudentLeaderBoard,Holiday
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializer import Eventserializer,NotificationSerilizer
from django.contrib.auth import update_session_auth_hash 
import pandas as pd
from django.db import transaction
from django.db.models.functions import ExtractMonth
from django.db.models.functions import Cast
from django.db.models import IntegerField
from ClassSphere.decorators import role_required
from rest_framework import status


def base_page(request):
 return render(request,'UserPages/base.html',{'user':request.user})

def sidebar(request):
    return render(request,'sidebar.html',{'user':request.user})

@login_required(login_url='login/')
def LandingPage(request):
    if request.user.is_authenticated:
        return render(request, 'UserPages/landingpage.html',{'user':request.user})
    else:
        return redirect('login')

def generate_random_id():
    prefix = "CSP"
    random_number = random.randint(1000000, 9999999)  
    return f"{prefix}{random_number}"

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
                            instance=profile.objects.all()
                            data=generate_random_id()  #CSP2033
                            for i in instance: #all userobject
                                if i.student_id==data:
                                    data=generate_random_id()
                            user_profile = profile.objects.create(newprofile=newuser,role=roleuser,grade=grade,payment_structure=paymentstructure,student_id=data)
                            user_profile.save()
                            return redirect('login')
                    else:
                        messages.error(request, "Passwords do not match.")
            elif 'back' in request.POST:
                return redirect('login')
    return render(request, 'UserPages/Register.html',context)

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
    return render(request, 'UserPages/Login.html')

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
    return render(request, 'UserPages/otp.html')

@login_required(login_url='login/')
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
        return render(request,'UserPages/ForgotPassword.html')

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
        return render(request, 'UserPages/passwordreset.html')

def event(request):
    return render(request,'UserPages/event.html')


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
    serializer=Eventserializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response({" Status ":serializer.errors})
    
@api_view(['PATCH'])
def update_events(request,id):
    try:
        instance = Event.objects.get(id=id)
    except Event.DoesNotExist:
        return Response({'Error': f'Event with id {id} not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer= Eventserializer(instance,data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response({'Error': f' Error code : {status.HTTP_400_BAD_REQUEST} , Invalid Payload '})
    
@role_required('Admin')
@api_view(['DELETE'])
def delete(request,id):
    event=get_object_or_404(Event,pk=id)
    try:
        event.delete()
    except: 
        return Response('Event not found')
    return Response('Event deleted successfully')

@role_required('admin')
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

@login_required(login_url='/login')
@role_required('Admin')
def eventCRUD(request):
    return render(request,'AdminPages/eventCrud.html')

@api_view(['POST'])
def filterevents(request):
    title = request.data.get('title', None)
    paidstatus = request.data.get('paidstatus', None)
    time_filter = request.data.get('timeFilter', None)
    tag=request.data.get('category',None)
    events = Event.objects.all() 
    if title:
        events = events.filter(title__icontains=title)
    if tag:
        events=events.filter(tag__icontains=tag)

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
    return Response({'events': event_data.data})

@api_view(['POST'])
def filterontag(request):
    data=request.data
    for key,value in data.items():
        events = Event.objects.all() 
        event_ins=events.filter(tag__icontains=value)
        event_data=Eventserializer(event_ins,many=True)
        print(event_data.data)
    return Response({'events':event_data.data})

# @role_required('Student')
# @login_required(login_url='/login/')
# def make_payment(request):
#     userprofile = request.user.profile
#     if request.method == 'POST':
#         amount_paid = request.POST.get('amount_paid')
#         payment = FeePayment(
#             student=userprofile,
#             amount_paid=int(amount_paid),
#         )
#         payment.save() 
#         current_user = request.user
#         try:
#             userprofile = profile.objects.get(newprofile=current_user)
#         except profile.DoesNotExist:
#             return Response({"error": "Profile not found."}, status=404)
#         fee = FeePayment.objects.filter(student=userprofile).first()
#         total_paid = 0
#         if fee:
#             total_paid = sum(payment.amount_paid for payment in userprofile.fee_payments.all())
#             total_fee_left = userprofile.payment_structure.Totalfeeamount - total_paid
#         else:
#             total_fee_left = userprofile.payment_structure.Totalfeeamount  
#     current_month = datetime.datetime.now().month
#     current_year = datetime.datetime.now().year
#     current_month_payments = FeePayment.objects.filter(
#         student=userprofile,
#         payment_date__year=current_year,
#         payment_date__month=current_month
#     )

    
#     is_fee_paid_this_month = current_month_payments.exists()
#     if not is_fee_paid_this_month:
#         notifications.objects.create(user_instance=userprofile,tag='Fees',NotificationMsg='Fee Pyment For this Month Pending Please Clear you Payment')
#     user=request.user
#     context = {
#         'userprofile': userprofile,
#         'amount_paid': total_paid,
#         'total_fee_left': total_fee_left,
#         'user':user
#     }
#     return render(request, 'UserPages/Payment.html', context)


@role_required('Student')
@login_required(login_url='/login/')
def make_payment(request):
    order_id=uuid.uuid4()
    print(order_id)
    usergrade = request.user.profile.grade
    usepayment_insatnce=PaymentStructure.objects.filter(grade=usergrade)
    paid_instance=FeePayment.objects.filter(student=request.user.profile)
    total_amount=0
    context={
        'user':request.user,
        'userprofile':request.user.profile,
        'uuid':order_id
    }
    for i in usepayment_insatnce:
        context['total_fee']=i.Totalfeeamount
        context['monthly_fee']=i.monthlyfee
    if paid_instance.exists():
        total_paid = sum(i.amount_paid for i in paid_instance)
        context['amount_paid'] = total_paid
        context['total_fee_left'] = context['total_fee'] - total_paid
        if context['total_fee_left']==0:
            context['paid_full']=True
    else:
        context['amount_paid'] = 0
        context['total_fee_left'] = context['total_fee']

    return render(request, 'UserPages/Payment.html',context)



@login_required
def process_payment(request):
    url = "https://dev.khalti.com/api/v2/epayment/initiate/"
    return_url=request.POST.get('return_url')
    order_id=request.POST.get('order_id')
    Total_amount=request.POST.get('amount')
    amount=int(Total_amount)*100
    user=request.user
    payload = json.dumps({
        "return_url": return_url,
        "website_url": "http://127.0.0.1:8000",
        "amount": amount,
        "purchase_order_id": order_id,
        "purchase_order_name": "test",
        "customer_info": {
        "name": user.username,
        "email":user.email
        }
    })
    headers = {
        'Authorization': 'key fe6413e5c26a4a13986749a8308403c0',
        'Content-Type': 'application/json',
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    res=json.loads(response.text)
    return redirect(res['payment_url'])
    
@login_required
def verifytransaction(request,amount):
    print(amount)
    print('view has been hit')
    pidx=request.GET.get('pidx')
    url = "https://dev.khalti.com/api/v2/epayment/lookup/"
    headers = {
        'Authorization': 'key fe6413e5c26a4a13986749a8308403c0',
        'Content-Type': 'application/json',
    }
    payload=json.dumps(
        {
        'pidx':pidx
    }
    )
    response = requests.request("POST", url, headers=headers, data=payload)
    new_res=json.loads(response.text)
    if new_res['status']=='Completed':
        userprofile=request.user.profile
        FeePayment.objects.create(student=userprofile,amount_paid=amount,payment_date=datetime.datetime.now())
    return redirect('pay')


@login_required
def eventdetail(request,id):
    event=Event.objects.get(id=id)
    event_obj={'obj':event}
    return render(request,'UserPages/eventdetail.html',context=event_obj)

@role_required('admin')
@api_view(['POST'])
def send_Notification(request):
    data=NotificationSerilizer(data=request.data)
    if data.is_valid():
        users=profile.objects.all()
        print(users)
        for user in users:
            print(user)
            message=data.validated_data['NotificationMsg']
            notifications.objects.create(NotificationMsg=message,user_instance=user)
        return JsonResponse({'Status':'Message sent Sucessfully'})
    else:
        return JsonResponse({'Status':data.errors})

@login_required
def profilepage(request):
    user = request.user
    role=request.user.profile.role
    grade_list = Grade.objects.all()
    userprofile_instance = profile.objects.get(newprofile=user)

    if request.method == 'POST':
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
        
    if userprofile_instance.grade:
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
            },
            'role':role
        }
    else:
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
                'grade': ""
            },
            'user':request.user
        }

    return render(request, 'UserPages/Userprofile.html', context)

@role_required('Student')
@login_required
def exam(request,id):
    ins=Exam.objects.get(id=id)
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
    elif ins.Exam_Date != datetime.date.today():
        messages.error(request,f'Please try again on {ins.Exam_Date}')
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
            return redirect('leaderboard')
    return render(request, 'UserPages/examquest.html', context)   

@api_view(['GET'])
def getallExam(request):
    exams = Exam.objects.all()
    result = {}
    for exam in exams:
        exam_key = f"{exam.Exam_Name}-{exam.id}"
        result[exam_key] = {
            'Exam_Date': str(exam.Exam_Date),
            'Total_Marks': exam.Total_Marks,
            'Questions': []
        }
        questions = Questions.objects.filter(Exam_Instace=exam)
        for q in questions:
            question_data = {
                'Question_Name': q.Question_Name,
                'Question_Marks': q.Question_Marks,
                'Correct_Answer': q.correct_answer,
                'Choices': []
            }

            choices = Choice.objects.filter(question_id=q.id)
            for c in choices:
                question_data['Choices'].append({
                    'Choice': c.choice_name
                })

            result[exam_key]['Questions'].append(question_data)

    return Response({"status": True, "data": result})


def leader_board(request):
    leaderboard=StudentLeaderBoard.objects.all().order_by('-total_marks')
    context={   
        "context":leaderboard
    } 
    return render(request,'UserPages/Leaderboard.html',context)

@role_required('Student')
@login_required
def schedule(request):
    user=request.user
    UserDatas=StudentLeaderBoard.objects.filter(student_id=user)
    answers=[]
    taken_exam_ids = StudentLeaderBoard.objects.filter(student_id=user).values_list('exam_id')
    available_exams = Exam.objects.exclude(id__in=taken_exam_ids)
    totalAttemptedExam=0
    today=datetime.date.today()
    for data in UserDatas:
        totalAttemptedExam+=1
        answers.append(data.total_marks)
    if answers:
        average = sum(answers) / len(answers)
        highestScore=max(answers)
    else:
        average = 0
        highestScore = 0
    exam=Exam.objects.all()
    context={
        'Attempts':totalAttemptedExam,
        'exam':exam,
        'avg_score':average,
        'higest_score':round(highestScore/100*100),
        'upcoming_exam':available_exams,
        'today':today
        }
    return render(request,'UserPages/exam.html',context)

@role_required('Admin')
@login_required
def attendance_view(request):
    attendance_records = attendance.objects.all().select_related('user')
    total_students = profile.objects.filter(role='Student').count()
    present= attendance.objects.filter(Attendance_Status='Present',date=datetime.date.today()).count()
    absent= attendance.objects.filter(Attendance_Status='absent',date=datetime.date.today()).count()
    percent=round(present/total_students*100)
    grades=Grade.objects.all()
    context = {
        'attendance':  attendance_records,
        'total_Student': total_students,
        'present':present,
        'absent':absent,
        'percent':percent,
        'grades':grades,
        'user':request.user
    }
    return render(request, 'AdminPages/attendance.html', context)  

@api_view(['POST'])
def get_attendance_data(request):
    if 'file' not in request.FILES:
        return Response({'Status': 'No file received'}, status=400)
    uploaded_file = request.FILES['file']
    if not uploaded_file.name.endswith('.xlsx'):
                return Response({'error': 'Only .xlsx files are allowed'}, status=400)
    else:
        required_columns=['Name','Email','Class','Date','Attendance Status']
        df=pd.read_excel(uploaded_file)
        records = df.to_dict('records')  
        colums=df.columns
        for i in required_columns:
            if i  not in  colums:
                print(f'{i} is not found in the excel sheet')   
                return Response({'ColumnError': f'No Column named {i} not  Found .Please check the File Format  '})
        for i in records:
            if not User.objects.filter(email=i['Email']).exists():
                return Response({"UserError": f"No user {i['Name']} exists in the system"})
            else:
                user_instance=User.objects.get(email=i['Email'])
                data=attendance.objects.filter(user=user_instance,date=i['Date'])
                if not  data:
                    attendance.objects.create(user=user_instance,Grade=user_instance.profile.grade,date=i['Date'],Attendance_Status=i['Attendance Status'])
    return Response({'Status': f'{uploaded_file.name} file received successfully'})

@api_view(['POST'])
def get_filter(request):
    body = request.data
    filtered_data = attendance.objects.all()
    if 'class' in body:
        filtered_data = filtered_data.filter(Grade__classname__icontains=body['class'])
    if 'date' in body:
        filtered_data = filtered_data.filter(date=body['date'])
    if 'status' in body:
        filtered_data = filtered_data.filter(Attendance_Status__icontains=body['status'])
    if 'name' in body:
        filtered_data = filtered_data.filter(user__first_name__icontains=body['name'])
    filtered_data = filtered_data.order_by('date')  
    data = []
    for item in filtered_data:
        data.append({
            'student_id': item.user.profile.student_id ,  
            'Name': f'{item.user.first_name} {item.user.last_name}',
            'Class': item.Grade.classname,
            'Date': item.date,
            'Status': item.Attendance_Status,
        })

    return Response({'status': data})
    
def holiday(request):
    holiday_date=Holiday.objects.all()
    return render(request,'UserPages/Holiday.html',{'holiday':holiday_date})

@role_required('Teacher')
def Exam_create(request):
    user=request.user
    return render(request,'AdminPages/ExamCreate.html',{'user':user})

@role_required('Teacher')
@api_view(['POST'])
def handlecreate(request):
    data=request.data   
    try:
        with transaction.atomic():
            grade_instance=Grade.objects.get(classname=data.get('exam_grade')) 
            exam_instance=Exam.objects.create(Exam_Name=data.get('exam_name'),ExamGrade=grade_instance,Exam_Date=data.get('exam_date'),Created_by=request.user,Total_Marks=data.get('total_marks'))
            question=data.get('questions')
            for i in question:
                question_instance=Questions.objects.create(Exam_Instace=exam_instance,Question_Name=i['question_text'],Question_Marks=i['marks'],correct_answer=i['correct_answer'])
                for choices,value in i['options'].items():
                    print(choices,value)
                    Choice.objects.create(choice_name=value,question_id=question_instance)
    except Exception as e:
        print('Somenthing went wonrg:',e)
    return Response({'status':data})     




@role_required('Teacher','Admin')
def adminpage(request):
    total_user=User.objects.count()
    total_eaxms=Exam.objects.count()
    total_tecahers=profile.objects.filter(role='Teacher').count()
    print(total_tecahers)
    listo = []  # List to store the total for each month
    for month in range(1, 13):  
        total = 0  
        data = FeePayment.objects.annotate(month=ExtractMonth('payment_date')).filter(month=month)
        for i in data:
            total += i.amount_paid  
        listo.append(total)  
    sumd=sum(listo)/1000
    context = {
        'data': listo,
        'total_user':total_user,
        'total_exams':total_eaxms,
        'total_revenue':round(sumd),
        'total_tecahers':total_tecahers
        }
    return render(request, 'AdminPages/admin.html', context)

@role_required('Admin')
def holidayCRUD(request):
    holiday_data = Holiday.objects.all()
    return render(request, 'AdminPages/Holidayadmin.html',{'holiday':holiday_data})

@api_view(['POST'])
def add_holiday(request):
    name = request.data.get('holiday')
    sdate = datetime.datetime.strptime(request.data.get('start_date'), "%Y-%m-%d").date()
    rdate = datetime.datetime.strptime(request.data.get('resume_date'), "%Y-%m-%d").date()
    overlapping_holidays = Holiday.objects.filter(Holiday_Date__lte=rdate).filter(School_ResumeDate__gte=sdate)
    if overlapping_holidays.exists():
        return Response({
            "Status": "Same Holiday Dates Found ",
            "Message": "A holiday already exists within the selected date range."
        }, status=400)

   
    Holiday.objects.create(
            Holiday_Name=name,
            Holiday_Date=sdate,
            School_ResumeDate=rdate,
        )
    users = profile.objects.all()
    for user in users:
            notifications.objects.create(
                Notificationtitle='Test Holiday',
                NotificationMsg=f'The school will remain closed from {sdate}  . Classes will continue from {rdate}.',
                user_instance=user,
                created_at=datetime.datetime.today(),
                tag='General',
                is_read=False
            )
    return Response({"Status": "Holiday Created Successfully"})

@role_required('Admin')
@api_view(['DELETE'])
def deleteHoliday(request,id):
    instance=Holiday.objects.get(id=id)
    instance.delete()
    return Response({"Status":"Holiday Deleted Sucessfully"})

@role_required('Admin')
def fee_setup(request):
    user=request.user
    fees = PaymentStructure.objects.annotate(classname_int=Cast('grade__classname', output_field=IntegerField())).order_by('classname_int')
    return render(request,'AdminPages/feesetup.html',{'user':user,'fees':fees})

@role_required('Admin')
@api_view(['UPDATE'])
def updatefee(request,id):
    body=request.data
    print(body)
    grade=int(request.data.get('Grade'))
    instance=Grade.objects.get(classname=grade)
    data=PaymentStructure.objects.filter(id=id).update(grade=instance,Totalfeeamount=request.data.get('total_fee'),AdmissionFee=request.data.get('admission_fee'))
    return Response({'status':'Sucessfully Updated The  data'})

@role_required('Admin')
@api_view(['DELETE'])
def deletefee(request,id):
    data=PaymentStructure.objects.get(id=id)
    print(data)
    data.delete()
    return Response({'status':'Data Deleted sucessfully'})


@login_required(login_url='/login/')
def notificationpage(request):
    user=request.user
    data=notifications.objects.filter(user_instance=user.profile)
    data_ins=notifications.objects.filter(user_instance=request.user.profile)
    for notification_object in data_ins:
        notification_object.is_read=True
        notification_object.save()
    return render(request,'UserPages/Notification.html',{'objects':data})



def erropage(request):
    return render(request,'Include and Base Pages/ErrorPage.html')