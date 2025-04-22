from django.shortcuts import redirect
class Handle404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        response = self.get_response(request)
          # Skip middleware for Khalti verification URLs
        if request.path.startswith('/verify/'):
            return response 
        if response.status_code == 404:
            return redirect('errorpage')
        return response
