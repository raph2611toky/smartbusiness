from django.shortcuts import render
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.views.decorators.cache import never_cache
from django.conf import settings
from dotenv import load_dotenv
import os
import functools

load_dotenv()

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def swagger_password_protect(view_func):
    @never_cache
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        SWAGGER_PASSWORD = os.getenv('SWAGGER_PASSWORD')
        if request.session.get('swagger_authenticated', False):
            return view_func(request, *args, **kwargs)

        if request.method == "POST":
            entered_password = request.POST.get("password", "").strip()
            if entered_password == SWAGGER_PASSWORD:
                request.session['swagger_authenticated'] = True
                request.session.modified = True 
                request.session.set_expiry(3600)
                return redirect(request.path)

            else:
                return render(request, "swagger_login.html", {
                    "error": "Mot de passe incorrect"
                })

        return render(request, "swagger_login.html")

    return wrapper