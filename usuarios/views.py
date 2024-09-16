from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Gastos, User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import UserRegistrationForm
from datetime import datetime, timedelta

# Create your views here.

#Verificação index
def index(request):

    
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    gastos = Gastos.objects.filter(usuario=request.user)


    return(render(request, "usuarios/usuario.html", {
        "gastos": gastos
    }))

#Página de login // Em breve cadastro
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

#Página de logout retornando o login
def logout_view(request):
    logout(request)
    return render(request, "usuarios/login.html", {
        "mensagem": "Logout realizado com sucesso!"
    })

#Pagina de criação de gastos // em breve data
def criar_gasto(request):

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    if request.method == "POST":
        cartao = request.POST.get("cartao").capitalize()
        categoria = request.POST.get("categoria")
        item = request.POST.get("item").capitalize()
        valor = float(request.POST.get("valor"))
        parcelas = int(request.POST.get("parcelas"))
        data_inicial = request.POST.get("data_inicial")
        usuario = request.user
        copia_mes = data_inicial[5:7:]
        copia_ano = data_inicial[2:4:]
        data_inicial_formatada = copia_mes + "/" + copia_ano
        p = Gastos(cartao=cartao, categoria=categoria, item=item, valor=valor, parcelas=parcelas, data_inicial=data_inicial_formatada, usuario=request.user)
        p.save()

        # Lógica para dividir o valor em parcelas


        return redirect('criar_gasto')
    
    
    
    gastos = Gastos.objects.filter(usuario=request.user)
    
    return render(request, "usuarios/usuario.html", {
        "gastos": gastos,
    })



#Páguna de visualizar gastos individualmente // em breve gráficos
def gastosIndividuais(request):

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    cartoes = Gastos.objects.filter(usuario=request.user).values_list('cartao', flat=True).distinct()
    cartoes_filtrados = None

    if request.method == "POST":
        cartao_buscado = request.POST.get("cartao")
        cartoes_filtrados = Gastos.objects.filter(cartao=cartao_buscado, usuario=request.user)
    
    return render(request, 'usuarios/gastosIndividuais.html', {
        'cartoes': cartoes,
        'gastos': cartoes_filtrados
    })


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('login')  # Redirecionar após o cadastro
        else:
            return render(request, 'usuarios/register.html', {'form': form, 'erro': 'Verifique os dados fornecidos.'})
    else:
        form = UserRegistrationForm()
    return render(request, 'usuarios/register.html', {'form': form})