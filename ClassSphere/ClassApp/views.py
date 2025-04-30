import datetime
import random
import uuid
import requests
import json
from django.http import  HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail,EmailMessage
from django.conf import settings
from .models import  profile,Event,Grade,Notification as notifications,PaymentStructure,FeePayment,Exam,Questions,Choice,attendance,User,StudentLeaderBoard,Holiday
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
from django.utils.safestring import mark_safe


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
    gradeoptions = Grade.objects.all()
    context = {'grades': gradeoptions}
    
    if request.user.is_authenticated:
        return redirect('homepage')
    
    if request.method == 'POST':
        if 'signup' in request.POST:
            roleuser = request.POST.get('role')
            grade_id = request.POST.get('Grade')
            grade = Grade.objects.get(id=grade_id)
            email = request.POST.get('remail')
            password2 = request.POST.get('rpassword2')
            password = request.POST.get('rpassword')
            paymentstructure = PaymentStructure.objects.get(grade=grade)
            char = "!@#$%^&*()-_=+[]{};:'\",.<>?/\\|`~"

            if len(password) < 10:
                messages.error(request, "Password must be at least 10 characters long.")
            elif not any(i in char for i in password):
                messages.error(request, "Password must contain at least one special character.")
            elif password != password2:
                messages.error(request, "Passwords do not match.")
            else:
                if User.objects.filter(email=email).exists():
                    messages.error(request, "Email already exists, use a different one.")
                else:
                    username = email.split("@")[0] if "@" in email else email
                    newuser = User.objects.create_user(username=username, email=email, password=password)
                    instance = profile.objects.all()
                    data = generate_random_id()
                    for i in instance:
                        if i.student_id == data:
                            data = generate_random_id()
                    
                    user_profile = profile.objects.create(
                        newprofile=newuser,
                        role=roleuser,
                        grade=grade,
                        payment_structure=paymentstructure,
                        student_id=data
                    )
                    user_profile.save()
                    return redirect('login')

        elif 'back' in request.POST:
            return redirect('login')

    return render(request, 'UserPages/Register.html', context)

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
                entered_otp = request.POST.get('ottp').strip()
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

@login_required(login_url='login')
def logouted(request):
    logout(request)
    return redirect('login')


def forgetpass(request):
    if request.method == 'POST':
        email = request.POST.get('forgotemail')
        try:
            user = User.objects.get(email=email)  
            request.session['workflow'] = 'Forgetpassword'
            otp = random.randint(100000, 999999)
            request.session['ottp'] = otp
            request.session['email'] = email
            request.session['isloggedin?'] = True
            print(otp)
            subject = "OTP for your ClassSphere Login"
            message = f"Dear User, {otp} is your OTP for ClassSphere password Reset. For security reasons, do not share it with others. Best regards, ClassSphere."
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]
            
            try:
                send_mail(subject, message, from_email, recipient_list)
                messages.success(request, "OTP has been sent to your email!")
                return redirect('ottp')
            except Exception as e:
                print(f"Error sending email: {e}")
                messages.error(request, "Error sending OTP. Please try again.")
                return render(request, 'UserPages/ForgotPassword.html')
                
        except User.DoesNotExist:
            messages.error(request, "Invalid Email. Please Try again.")
    return render(request, 'UserPages/ForgotPassword.html')

def reset(request):
    if not request.session.get('isloggedin?',False):
        return redirect('homepage')
    else:
        if request.method == 'POST':  
            password2 = request.POST.get('rpassword2')
            password = request.POST.get('rpassword')
            if password != password2:
                messages.error(request, "Passwords do not match.")
                return render(request, 'UserPages/passwordreset.html')

            if password is None or password2 is None:
                messages.error(request, "Please enter both password fields.")
                return render(request, 'UserPages/passwordreset.html')
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
    required_fields = ['email', 'subject', 'message']
    for field in required_fields:
        if field not in postdata:
            return Response({"status": "Missing required fields"}, status=400)
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
        return Response(response_data, status=200)

@api_view(['GET'])
def getevents(request):
 events=Event.objects.all()
 serializer=Eventserializer(events,many=True)
 return JsonResponse(serializer.data,safe=False)

@api_view(['POST'])
def create_event(request):
    if not request.data:
        return Response({" Error ":"No data passed "})
    serializer=Eventserializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response({" Status ":serializer.errors})
    
@role_required('Admin')
@api_view(['PATCH'])
def update_events(request,id):
    try:
        instance = Event.objects.get(id=id)
    except Event.DoesNotExist:
        return Response({'Error': f'Event with id {id} not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer= Eventserializer(instance,data=request.data,partial=True)
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

@api_view(['GET'])
def geteventbyid(request,id):
    event=Event.objects.get(id=id)
    serializer=Eventserializer(event)
    return JsonResponse(serializer.data)

@api_view(['POST'])
def filterevents(request):
    filtertags = {'title', 'paidstatus', 'time_filter', 'category'}
    invalid_tags = [i for i in request.POST if i not in filtertags]

    if invalid_tags:
        return Response(
            {'error': f'Invalid filter tag: {", ".join(invalid_tags)}'},
            status=400
        )
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

@login_required
def eventdetail(request,id):
    event=Event.objects.get(id=id)
    event_obj={'obj':event}
    return render(request,'UserPages/eventdetail.html',context=event_obj)

@login_required(login_url='/login')
@role_required('Admin')
def eventCRUD(request):
    return render(request,'AdminPages/eventCrud.html')

@role_required('Student')
@login_required(login_url='/login/')
def make_payment(request):
    order_id=uuid.uuid4()
    userprofile=request.user.profile
    usergrade = request.user.profile.grade
    usepayment_insatnce=PaymentStructure.objects.filter(grade=usergrade)
    paid_instance=FeePayment.objects.filter(student=request.user.profile)
    total_amount=0
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    current_month_payments = FeePayment.objects.filter(
         student=userprofile,
         payment_date__year=current_year,
         payment_date__month=current_month
     )
    is_fee_paid_this_month = current_month_payments.exists()
    if not is_fee_paid_this_month:
         notifications.objects.create(user_instance=userprofile,tag='Fees',NotificationMsg='Fee Pyment For this Month Pending Please Clear you Payment')
    context={
        'user':request.user,
        'userprofile':request.user.profile,
        'uuid':order_id,
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

@api_view(['POST'])
@login_required
def process_payment(request):
    url = "https://dev.khalti.com/api/v2/epayment/initiate/"
    return_url=request.POST.get('return_url')
    order_id=request.POST.get('order_id')
    Total_amount=request.POST.get('amount')
    try:
        Total_amount = request.data.get('amount')
        amount = int(Total_amount)*100

    except ValueError:
        return Response({'status': 'Invalid Amount'}, status=status.HTTP_400_BAD_REQUEST)
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
        'Authorization': f'key {settings.KHALTI_API_KEY}',
        'Content-Type': 'application/json',
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.text:
        res = json.loads(response.text)
    else:
        return Response({'error': 'Empty response from server'}, status=400)
    return redirect(res['payment_url'],amount)

@login_required
def verifytransaction(request,amount):
    print(amount)
    try:
        amount = int(amount)
    except ValueError:
        return Response({'status':'Invalid Amount'},status=status.HTTP_400_BAD_REQUEST)
    pidx=request.GET.get('pidx')
    url = "https://dev.khalti.com/api/v2/epayment/lookup/"
    headers = {
        'Authorization': f'key {settings.KHALTI_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload=json.dumps({'pidx':pidx})
    response = requests.request("POST", url, headers=headers, data=payload)
    new_res=json.loads(response.text)
    print(new_res)
    if new_res.get('status') == 'Completed':
        print('hit vayo')
        try:
            userprofile=request.user.profile
            FeePayment.objects.create(student=userprofile,amount_paid=amount,payment_date=datetime.datetime.now(),grade=userprofile.grade)
        except Exception as  e:
            return Response({'Error':f"{str(e)}"})

    return redirect('pay')

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
    print(user.profile.address)
    if request.method == 'POST':
        print(request.POST) 
        if 'Savedetails' in request.POST:
            print(request.POST)
            fname = request.POST.get('fname', '').strip()
            lname = request.POST.get('lname', '').strip()
            username = request.POST.get('username', '').strip()
            address=request.POST.get('address','').strip()
            updated = False
            if fname:
                user.first_name = fname
                updated = True
            if lname:
                user.last_name = lname
                updated = True
            if address:
                UserProfile=profile.objects.get(newprofile=request.user)
                UserProfile.address=address
                UserProfile.save()
            if username:
                user.username = username
                updated = True
            if updated:
                print('updated')
                user.save()
                return JsonResponse({'status':'Profile Has been updated sucessfully'})
        elif 'OTPconfirm' in request.POST:
            email=request.user.email
            otp = random.randint(100000, 999999)
            print(otp)
            request.session['ottp'] = otp  
            request.session['email'] = email 
            subject = "OTP for your ClassSphere Login"
            message = f"Dear User,You OTPfor Email chnage is {otp}. For security reasons, do not share it with others. Best regards, ClassSphere."
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]
            try:
                    send_mail(subject, message, from_email, recipient_list)
            except Exception as e:
                    print(f"Error sending email: {e}")
        elif 'ResentOTP' in request.POST:
            email=request.user.email
            otp = random.randint(100000, 999999)
            print(otp)
            request.session.pop('ottp', None)
            request.session.pop('email', None)
            request.session['ottp'] = otp  
            request.session['email'] = email 
            subject = "OTP for your ClassSphere Login"
            message = f"Dear User,You OTPfor Email chnage is {otp}. For security reasons, do not share it with others. Best regards, ClassSphere."
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]
            try:
                    send_mail(subject, message, from_email, recipient_list)
            except Exception as e:
                    print(f"Error sending email: {e}")
        elif 'OTP'  in request.POST:
            userOTP=request.POST.get('OTP')
            newemail=request.POST.get('newemail')
            stores_otp=request.session.get('ottp')
            if str(userOTP)==str(stores_otp):
                user=request.user
                user.email=newemail
                user.save()
                request.session.pop('ottp', None)
                request.session.pop('email', None)
                messages.success(request,'Email Changed sucessfully')
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
                'address':user.profile.address
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
    result = []  
    for exam in exams:
        exam_data = {
            'Exam_ID': exam.id,
            'Exam_Name': exam.Exam_Name,
            'Exam_Date': str(exam.Exam_Date),
            'Total_Marks': exam.Total_Marks,
            'Questions': []
        }

        questions = Questions.objects.filter(Exam_Instace=exam)
        for q in questions:
            question_data = {
                'Question_Id':q.id,
                'Question_Name': q.Question_Name,
                'Question_Marks': q.Question_Marks,
                'Correct_Answer': q.correct_answer,
                'Choices': []
            }

            choices = Choice.objects.filter(question_id=q.id)
            for c in choices:
                question_data['Choices'].append({
                    "id": c.id,
                    'Choice': c.choice_name
                })

            exam_data['Questions'].append(question_data)

        result.append(exam_data)  # Append exam_data to the result list

    return Response({"status": True, "data": result})

@login_required(login_url='login/')
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
            exam_instance=Exam.objects.create(Exam_Name=data.get('exam_name'),ExamGrade=grade_instance,Exam_Date=data.get('exam_date'),Total_Marks=data.get('total_marks'))
            question=data.get('questions')
            for i in question:
                question_instance=Questions.objects.create(Exam_Instace=exam_instance,Question_Name=i['question_text'],Question_Marks=i['marks'],correct_answer=i['correct_answer'])
                for choices,value in i['options'].items():
                    print(choices,value)
                    Choice.objects.create(choice_name=value,question_id=question_instance)
    except Exception as e:
        print('Somenthing went wonrg:',e)
    return Response({'status':data})   

@role_required('Teacher')
@login_required
def exam_managementpage(request):
    return render(request,'AdminPages/ExamUpdate.html')

@api_view(['PATCH'])
def updateexam(request):
    data = request.data
    rgrade = data.get('Grade')
    exam_id = data.get('Exam_ID')
    try:
        grade_ins = Grade.objects.get(classname=rgrade)
    except Grade.DoesNotExist:
        return Response({'error': 'Grade not found'}, status=status.HTTP_400_BAD_REQUEST)


    exam_instance = Exam.objects.get(id=exam_id)
    with transaction.atomic():
        Exam.objects.filter(id=exam_id).update(
            Exam_Name=data.get('Exam_Name'),
            Total_Marks=data.get('Total_Marks'),
            Exam_Date=data.get('Exam_Date'),
            ExamGrade=grade_ins
        )

        for question_data in data.get('Questions', []):
            question_id = question_data.get('Question_Id')
            question = Questions.objects.filter(id=question_id).first()
            question = Questions.objects.create(
                    Exam_Instace=exam_instance,
                    Question_Name=question_data.get('Question_Name'),
                    Question_Marks=question_data.get('Question_Marks'),
                    correct_answer=question_data.get('correct_answer')
                )

            for choice_data in question_data.get('Choices', []):
                choice_id = choice_data.get('id')
                choice_text = choice_data.get('text')
                is_correct = choice_data.get('correct')

                if choice_id:
                    choice = Choice.objects.filter(id=choice_id).first()
                    if choice:
                        choice.choice_text = choice_text
                        choice.correct = is_correct
                        choice.save()
    return Response(data={'message':'Data Updates Sucessfully'}, status=status.HTTP_200_OK)

@login_required
@api_view(['DELETE'])
def deleteExam(request,id):
    eaxm=Exam.objects.get(id=id)
    eaxm.delete()
    return Response({'Status':'Deletes Sucessfully'},status=status.HTTP_200_OK)

@login_required(login_url='login/')
@role_required('Student')
def leader_board(request):
    leaderboard=StudentLeaderBoard.objects.all().order_by('-total_marks')
    context={   
        "context":leaderboard
    } 
    return render(request,'UserPages/Leaderboard.html',context)

@login_required(login_url='login/')
@role_required('Student')
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
        'Leaderboard':UserDatas,
        'avg_score':average,
        'higest_score':round(highestScore/100*100),
        'upcoming_exam':available_exams,
        'today':today
        }
    return render(request,'UserPages/exam.html',context)

@role_required('Admin')
@login_required(login_url='login/')
def attendance_view(request):
    attendance_records = attendance.objects.all().select_related('user')
    total_students = profile.objects.filter(role='Student').count()
    present= attendance.objects.filter(Attendance_Status='Present',date=datetime.date.today()).count()
    absent= attendance.objects.filter(Attendance_Status='Absent',date=datetime.date.today()).count()
    percent = 0
    if total_students > 0:
        percent = round((present / total_students) * 100)
    
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
@login_required(login_url='login/')
def get_attendance_data(request):
    if 'file' not in request.FILES:
        return Response({'UserError': 'No file received'}, status=400)
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
            try:
                user_instance = User.objects.get(email=i['Email'])
                
                if user_instance.profile.role in ['admin', 'teacher']:
                    return Response({"UserError": f"User {i['Name']} is an Admin or Teacher, not allowed."})
                
                attendance_data = attendance.objects.filter(user=user_instance, date=i['Date'])
                
                if not attendance_data.exists():
                    attendance.objects.create(
                        user=user_instance,
                        Grade=user_instance.profile.grade,
                        date=i['Date'],
                        Attendance_Status=i['Attendance Status'].capitalize()
                    )

            except User.DoesNotExist:
                return Response({"UserError": f"No user {i['Email']} exists in the system"})

    return Response({'Status': f'{uploaded_file.name} file received successfully'})

@api_view(['POST'])
@login_required(login_url='login/')
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

@login_required(login_url='login/') 
def holiday(request):
    holiday_date=Holiday.objects.all()
    return render(request,'UserPages/Holiday.html',{'holiday':holiday_date})

@login_required(login_url='login/')
@role_required('Teacher','Admin')
def adminpage(request):
    total_user=User.objects.count()
    total_eaxms=Exam.objects.count()
    total_tecahers=profile.objects.filter(role='Teacher').count()
   
    totalstudentbyclass=[0]*10
    for classname in range(1,11):
        for obj in profile.objects.filter(grade__classname=classname):
            totalstudentbyclass[classname-1]+=1
      
    listo = [] 
    for month in range(1, 13):  
        total = 0   
        data = FeePayment.objects.annotate(month=ExtractMonth('payment_date')).filter(month=month)
        for i in data:
            total += i.amount_paid  
        listo.append(total)  
    sumd=sum(listo)/1000
    total_Grade_fee = []
    Outstanding = []

    for obj in range(1, 11):
        grade_instance = Grade.objects.get(classname=obj)
        
        Gradedata = PaymentStructure.objects.get(grade=grade_instance)
        Total_fees = Gradedata.Totalfeeamount
        total_Grade_fee.append(Total_fees)
        
        total_collected = 0
        fee_payments = FeePayment.objects.filter(grade=grade_instance)
        for payment in fee_payments:
            total_collected += payment.amount_paid

        outstanding_amount = Total_fees - total_collected
        Outstanding.append(outstanding_amount)


    print("All Grades - Total Fees:", total_Grade_fee)
    print("All Grades - Outstanding:", Outstanding)

    context = {
        'data': listo,
        'total_user':total_user,
        'total_exams':total_eaxms,
        'total_revenue':round(sumd),
        'total_tecahers':total_tecahers,
        'totalstudentbyclass':totalstudentbyclass,
        'total_fee': mark_safe(json.dumps(total_Grade_fee)),
        'outstanding_fee': mark_safe(json.dumps(Outstanding)),
        }
    return render(request, 'AdminPages/admin.html', context)

@login_required(login_url='login/')
@role_required('Admin')
def holidayCRUD(request):
    holiday_data = Holiday.objects.all()
    return render(request, 'AdminPages/Holidayadmin.html',{'holiday':holiday_data})


@login_required(login_url='login/')
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

@login_required(login_url='login/')
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
    return Response({'status':'Data Deleted sucessfully'}) #optional
 
@login_required(login_url='/login/')
def notificationpage(request):
    user=request.user
    data=notifications.objects.filter(user_instance=user.profile).order_by('is_read')
    count=0
    for i in data:
        if i.is_read == False:
            count+=1
    print(count)
    return render(request,'UserPages/Notification.html',{'objects':data,'count':count})

@api_view(['POST'])
def mark_as_read(request):
    if request.method=='POST' :
        requestdata=request.data
        print(requestdata['id'])
        instance=notifications.objects.get(id=requestdata['id'])
        instance.is_read=True
        instance.save()
    return Response({'status':'Data Updated Sucessfully'})

def erropage(request):
    return render(request,'Include and Base Pages/ErrorPage.html')

@api_view(['GET'])
def get_FilterData(request, id):
    instance = Exam.objects.get(id=id)
    queryset = StudentLeaderBoard.objects.filter(exam_id=instance).order_by('-exam_id__Exam_Date')
    Data = []
    for obj in queryset:
        exam = obj.exam_id  
        exam_data = {
            'id': exam.id,
            'Exam_Name': exam.Exam_Name,
            'ExamGrade': exam.ExamGrade.id, 
            'Exam_Date': exam.Exam_Date,
            'Total_Marks': exam.Total_Marks,
        }
        Data.append({
            'id': obj.id,
            'exam_instance': exam_data,
            'user_id': obj.student_id.id,
            'score': obj.Correct,
            'Incorrect': obj.Incorrect,
            'Answered': obj.Answered,
            'Total_Question': obj.Total_Question,
        })
    return Response({'Data': Data})

@role_required('Admin')
@login_required(login_url='login/')
def user_management(request):
    users = User.objects.all() 
    now = datetime.datetime.now()
    user_data = [] 

    for student in users:  
        try:
            userprofile = student.profile 
        except profile.DoesNotExist:
            continue  

        has_paid = FeePayment.objects.filter(
            student=userprofile,
            payment_date__year=now.year,
            payment_date__month=now.month
        ).exists()

        user_data.append({
            'user': student,    
            'paid': has_paid,
            'is_active': student.is_active,
        })

    context = {
        'users': user_data,
        'inactive_users': User.objects.filter(is_active=False),  # Optional if needed separately

    }
    return render(request, 'UserPages/UserManagement.html', context)

@api_view(['POST'])
def update_user(request):
    username = request.POST.get('username')
    newrole = request.POST.get('newrole')
    print(newrole)
    reason = request.POST.get('reason')
    grade_value = request.POST.get('grade')

    try:
        user = User.objects.get(username=username)
        user_profile = profile.objects.get(newprofile=user)
        if newrole == 'Admin':
            user_profile.grade = None
            user_profile.payment_structure = None
            data=FeePayment.objects.filter(student=user_profile)
            examrecords=StudentLeaderBoard.objects.filter(student_id=user)
            for i in examrecords:
                i.delete()
            for obj in data:
                obj.delete()
        elif newrole == 'Teacher':
            grade_obj = Grade.objects.get(classname=grade_value)
            user_profile.grade = grade_obj
            user_profile.payment_structure = None
            data=FeePayment.objects.filter(student=user_profile)
            for i in examrecords:
                i.delete()
            for obj in data:
                obj.delete()
        elif newrole=='Student':
            grade_obj = Grade.objects.get(classname=grade_value)
            print(grade_obj)
            payment_structure = PaymentStructure.objects.get(grade=grade_obj)
            user_profile.grade = grade_obj
            user_profile.payment_structure = payment_structure
        user_profile.role = newrole
        user_profile.save()
        send_mail(
            subject='Your Role Has Been Updated',
            message=f'Hello {user.username},\n\nYour role has been updated to "{newrole}".\nReason: {reason}\n\nThank you.',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({'message': 'User role updated and email sent successfully.'})

    except Exception as e:
        print("Error occurred:", str(e))
        return Response({'error': str(e)}, status=500)

    except Exception as e:
        print("Error occurred:", str(e))  
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
def ban(request):
    username=request.POST.get('username')
    typeof=request.POST.get('ban_type')
    reason=request.POST.get('reason')
    user=User.objects.get(username=username)
    user.is_active=False
    user.save()
    send_mail(
            subject='Regarding Account Deactivation',
            message=f'Hello {user.username},\n\nYour Account For ClassSpher Has been banned {typeof} Due to {reason} . Please contact Student Help Desk For more Information',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
    return Response({'status':f'{username} has been banned from loggin onto the ystem '})


