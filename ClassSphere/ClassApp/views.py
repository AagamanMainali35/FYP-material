from django.shortcuts import render

# Create your views here.
def LandingPage(request):
    return render(request,'landingpage.html')

def loginPage(request):
    return render(request,'Login.html')