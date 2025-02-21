from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import datetime
from django.utils import timezone

# Helper function to get the current academic year
def get_academic_year():
    current_year = datetime.datetime.now().year
    return f"{current_year}/{current_year + 1}"

# Grade Model
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
        return f'Grade {self.classname}--{self.academic_year}'
    
    class Meta:
        unique_together = ['classname', 'academic_year']
        db_table = 'grade_table'

# PaymentStructure Model
class PaymentStructure(models.Model):
    grade = models.OneToOneField(Grade, on_delete=models.CASCADE, related_name="payment_structure")
    Totalfeeamount = models.IntegerField()  # Total fee for the grade
    AdmissionFee = models.IntegerField()    # Admission fee for the grade

    @property
    def monthlyfee(self):
        return self.Totalfeeamount / 12  # Calculate monthly fee
    
    def __str__(self):
        return f'Grade {self.grade.classname}'

# Profile Model
class profile(models.Model):
    ROLE = [
        ('Teacher', 'Teacher'),
        ('Student', 'Student'),
    ]
    newprofile = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(verbose_name='Role', choices=ROLE, max_length=10)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, null=True, blank=True)
    payment_structure = models.ForeignKey(PaymentStructure, on_delete=models.CASCADE, null=True, blank=True, related_name='profiles')

    def clean(self):
        if self.role == 'Student' and not self.grade:
            raise ValidationError({'grade': 'Grade is required for students.'})

    def __str__(self):
        return self.newprofile.email

class FeePayment(models.Model):
    student = models.ForeignKey(profile, on_delete=models.CASCADE, related_name='fee_payments')
    amount_paid = models.IntegerField() 
    payment_date = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return f'{self.student.newprofile.email} - {self.amount_paid}'

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
    title = models.CharField(max_length=100)
    is_paid = models.BooleanField(default=False)
    eventbanner = models.ImageField(upload_to='EventBanners')
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=100)
    form = models.FileField(upload_to='forms/', null=True, blank=True)

    def __str__(self):
        return self.title

# Notification Model
class Notification(models.Model):
    NotificationMsg = models.CharField(max_length=500)
    user = models.ForeignKey(profile, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.id}--{self.NotificationMsg}'