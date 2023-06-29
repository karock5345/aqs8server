from django.http import HttpResponseForbidden

def superuser_required(view_func):
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden("You must be a superuser to access this resource.")
        return view_func(request, *args, **kwargs)
    return wrapped_view