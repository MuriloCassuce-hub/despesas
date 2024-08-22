from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout

# Create your views here.

def index(request):
    
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    return(render(request, "usuarios/usuario.html"))

def login_view(request):
    
    if request.method=="POST":
        usuario = request.POST.get("usuario")
        senha = request.POST.get("senha")
        usuario = authenticate(request, username = usuario, password = senha)
        
        if usuario is not None:
            login(request, usuario)
            return HttpResponseRedirect(reverse("index"))
        
        else:
            return render(request, "usuarios/login.html", {
                "mensagem": "Credenciais inválidas"
            })
    
    return render(request, "usuarios/login.html")

def logout_view(request):
    logout(request)
    return render(request, "usuarios/login.html", {
        "mensagem": "Logout realizado com sucesso!"
    })