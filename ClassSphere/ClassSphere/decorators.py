from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from ClassApp.models import *

def role_required(*required_roles):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            try:
                profile_isntace = request.user.profile
                if profile_isntace.role in required_roles:
                    return view_func(request, *args, **kwargs)
                else:
                    return redirect('errorpage')
            except profile.DoesNotExist:
                return HttpResponseForbidden("Profile not found.")
        return _wrapped_view
    return decorator
