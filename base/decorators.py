from django.http import HttpResponse
from django.shortcuts import redirect

def unauth_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated == False :          
            return redirect('login') 
        else:
            return view_func(request, *args, **kwargs)

    return wrapper_func


def unauth_user_login(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated == True :          
            return redirect('home') 
        else:
            return view_func(request, *args, **kwargs)

    return wrapper_func

def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):    
            group_name = None
            auth = False
            if request.user.groups.exists():
                groups = request.user.groups.all()
                for group in groups :
                    group_name = group.name
                    if group_name in allowed_roles:
                        auth = True
                        return view_func(request, *args, **kwargs)
            if request.user.is_superuser == True:
                auth = True
                return view_func(request, *args, **kwargs)
            if auth == False:
                return HttpResponse('You are not authorized to view the page')

        return wrapper_func
    return decorator