from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import datetime
def get_academic_year():
    current_year = datetime.datetime.now().year
    return f"{current_year}/{current_year + 1}"

class Grade(models.Model):
    option = [
        ('1', 'Grade 1'),
        ('2', 'Grade 2'),
        ('3', 'Grade 3'),
        ('4', 'Grade 4'),
        ('5', 'Grade 5'),
        ('6', 'Grade 6'),
        ('7', 'Grade 7'),
        ('8', 'Grade 8'),
        ('9', 'Grade 9'),
        ('10', 'Grade 10'),
    ]
    classname = models.CharField(choices=option, max_length=2) 
    academic_year = models.CharField(max_length=9, default=get_academic_year)
    
    def __str__(self):
        return f'Grade {self.classname}--{self.id}'
    
    class Meta:
        unique_together = ['classname', 'academic_year']
        db_table = 'grade_table'


class PaymentStructure(models.Model):
    grade = models.OneToOneField(Grade, on_delete=models.CASCADE, related_name="payment_structure")
    Totalfeeamount = models.IntegerField()  # Total fee for the grade
    AdmissionFee = models.IntegerField()    # Admission fee for the grade

    @property
    def monthlyfee(self):
        return self.Totalfeeamount / 12  # Calculate monthly fee
    
    def __str__(self):
        return f'Grade {self.grade.classname}'

class profile(models.Model):
    ROLE = [
        ('Teacher', 'Teacher'),
        ('Student', 'Student'),
        ('Admin', 'Admin'),
    ]
    student_id=models.CharField(null=True,blank=True)
    newprofile = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(verbose_name='Role', choices=ROLE, max_length=10)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, null=True ,blank=True)
    payment_structure = models.ForeignKey(PaymentStructure, on_delete=models.CASCADE, null=True,blank=True, related_name='profiles')
    profile_picture=models.ImageField(verbose_name='Enter Your Profile Picture here' ,null=True,blank=True ,upload_to='profilePictures0,',default='profilePictures/DefaultPP.jpg')

    def clean(self):
        if self.role == 'Student':
            if not self.grade:
                raise ValidationError({'grade': 'Grade is required for students.'})
            if not self.payment_structure:
                raise ValidationError({'payment_structure': 'Payment structure is required for students.'})
        elif self.role == 'Teacher':
            if not self.grade:
                raise ValidationError({'grade': 'Grade is required for teachers.'})
            if self.payment_structure:
                raise ValidationError({'payment_structure': 'Teachers should not have a payment structure.'})
        elif self.role == 'Admin':
            if self.grade:
                raise ValidationError({'grade': 'Admins should not have a grade.'})
            if self.payment_structure:
                raise ValidationError({'payment_structure': 'Admins should not have a payment structure.'})


    def __str__(self):
        return self.newprofile.email

class FeePayment(models.Model):
    student = models.ForeignKey(profile, on_delete=models.CASCADE, related_name='fee_payments')
    amount_paid = models.IntegerField() 
    payment_date = models.DateTimeField()  

    def __str__(self):
        return f' {self.id}-{self.student.newprofile.email} - {self.amount_paid}'

    @property
    def total_fee_left(self):
        if self.student.payment_structure:
            total_fee = self.student.payment_structure.Totalfeeamount  
            total_paid = 0
            for payment in self.student.fee_payments.all():
                total_paid += payment.amount_paid  
            return total_fee - total_paid
        return 0 


class Event(models.Model):
    tagchoices = [
    ('Music', 'Music'),
    ('Arts', 'Arts'),
    ('Sports', 'Sports'),
    ('Education', 'Education'),
    ('Drama', 'Drama'),
    ('Literature', 'Literature'),
    ('Computer Science', 'Computer Science'),
    ('Science', 'Science'),
    ('Mathematics', 'Mathematics'),
    ('Languages', 'Languages'),
    ('School Events', 'School Events'),
    ('Club Activities', 'Club Activities'),
    ('Robotics', 'Robotics'),
    ('Design', 'Design'),
    ('Leadership', 'Leadership'),
]
    title = models.CharField(max_length=100)
    is_paid = models.BooleanField(default=False)
    eventbanner = models.ImageField(upload_to='EventBanners')
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=100)
    form = models.URLField(blank=True,null=True)
    tag=models.CharField(choices=tagchoices,null=True,blank=True)
    def __str__(self):
        return self.title

class Notification(models.Model):
    tag=[
        ('Fees','Fees'),
        ('General','General'),
        ('Holiday','Holiday'),
        ('Exam','Exam'),
        ('Profile','Profile')
    ]
    NotificationMsg = models.CharField(max_length=500)
    user_instance = models.ForeignKey(profile, on_delete=models.CASCADE)
    created_at=models.DateField(default=datetime.date.today)
    tag=models.CharField(choices=tag,max_length=255,default='General')
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user_instance.id}--{self.NotificationMsg}'
 
class Exam(models.Model):
    Exam_Name=models.CharField(max_length=255,null=False)
    ExamGrade=models.ForeignKey(Grade,null=False,on_delete=models.CASCADE)
    Exam_Date=models.DateField(max_length=255,null=False)
    Created_by=models.ForeignKey(User,on_delete=models.CASCADE)
    Total_Marks=models.CharField(max_length=255,null=False)
    def __str__(self):
        return f'{self.Exam_Name[:50]}-{self.id}'
    
class Questions(models.Model): 
    Exam_Instace=models.ForeignKey(Exam,on_delete=models.CASCADE,null=False)
    Question_Name=models.CharField(max_length=255,null=False)
    Question_Marks= models.CharField(max_length=100,null=False)
    correct_answer=models.CharField(max_length=255,null=True)
    def __str__(self):
        return f'{self.Exam_Instace}-{self.Question_Name[:20]}'
    
class Choice(models.Model):
    choice_name=models.CharField(max_length=255,verbose_name='Answer',null=False)
    question_id=models.ForeignKey(Questions,on_delete=models.CASCADE,null=False)
    def __str__(self):
        return self.choice_name[:20]

class StudentAnswers(models.Model):
    question_id=models.ForeignKey(Questions,on_delete=models.CASCADE,null=False)
    user_id=models.ForeignKey(User,on_delete=models.CASCADE,null=False)
    StudentAnswers=models.CharField(verbose_name='Student_ID',max_length=255,null=True)
    def __str__(self):
        return f' question no {self.question_id.id} answered as {self.StudentAnswers} bu  {self.user_id.username}'
    
class StudentLeaderBoard(models.Model):
    exam_id=models.ForeignKey(Exam,on_delete=models.CASCADE)
    student_id=models.ForeignKey(User,on_delete=models.CASCADE)
    total_marks=models.IntegerField()
    Correct=models.IntegerField(null=True)
    Incorrect=models.IntegerField(null=True)
    Answered=models.IntegerField(null=True)
    Total_Question=models.IntegerField(null=True)

    def __str__(self):
        return self.exam_id.Exam_Name
    
class attendance(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    Grade=models.ForeignKey(Grade,on_delete=models.CASCADE)
    date=models.DateField()
    Attendance_Status=models.CharField(verbose_name='Attendnace Status',null=True)
    def __str__(self):
        return f'Attendance of {self.user.username} on date  {self.date}'
    

class Holiday(models.Model):
    Holiday_Name=models.CharField(max_length=300)
    Holiday_Date=models.DateField()
    End_DateField=models.DateField()
    School_ResumeDate=models.DateField()
    Duration=models.CharField(max_length=255,null=True,blank=True)
    Type=models.CharField(verbose_name='Type of Holiday')
    def save(self, *args, **kwargs):
        if self.Holiday_Date and self.School_ResumeDate:
            days = (self.School_ResumeDate - self.Holiday_Date).days
            self.Duration = f"{days} days"
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.Holiday_Name





