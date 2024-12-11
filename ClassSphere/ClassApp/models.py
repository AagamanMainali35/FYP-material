from django.db import models
from django.contrib.auth.models import User    
class profile(models.Model):
    ROLE=[
        ('Teacher','Teacher'),
        ('Student','Student'),
        ]
    GRADE_CHOICES = [
        (1, 'Grade 1'),
        (2, 'Grade 2'),
        (3, 'Grade 3'),
        (4, 'Grade 4'),
        (5, 'Grade 5'),
        (6, 'Grade 6'),
        (7, 'Grade 7'),
        (8, 'Grade 8'),
        (9, 'Grade 9'),
        (10, 'Grade 10'),
    ]
    newprofile=models.OneToOneField(User,on_delete=models.CASCADE)
    role=models.CharField(verbose_name='Role',choices=ROLE)
    grade=models.CharField(choices=GRADE_CHOICES,null=True,blank=True)

    def __str__(self):
        return self.newprofile.email