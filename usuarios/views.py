from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Gastos
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from .forms import UserRegistrationForm
import plotly.graph_objects as go
from collections import defaultdict
from decimal import Decimal
from datetime import datetime


#Verificação index
def index(request):

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    return HttpResponseRedirect(reverse("criar_gasto"))

#Página de login
def login_view(request):

    if request.method=="POST":
        usuario = request.POST.get("usuario")
        senha = request.POST.get("senha")
        usuario = authenticate(request, username = usuario, password = senha)
        if usuario is not None:
            login(request, usuario)
            return HttpResponseRedirect(reverse("criar_gasto"))
        
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

#Pagina de criação de gastos
def criar_gasto(request):

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))

    if request.method == "POST" and "criar_gasto" in request.POST:
        cartao = request.POST.get("cartao").capitalize()
        categoria = request.POST.get("categoria")
        item = request.POST.get("item").capitalize()
        valor = float(request.POST.get("valor"))
        parcelas = int(request.POST.get("parcelas"))
        parcelado = parcelas
        data_inicial = request.POST.get("data_inicial")
        usuario = request.user

        copia_mes = int(data_inicial[5:7])
        copia_ano = int(data_inicial[0:4])

        for i in range(1, parcelas + 1):
            parcela_atual = f"{i}/{parcelas}"
            if i == 1:
                data_inicial_formatada = f"{str(copia_mes).zfill(2)}/{str(copia_ano)}"
            else:
                copia_mes += 1
                if copia_mes > 12:
                    copia_mes = 1
                    copia_ano += 1
                data_inicial_formatada = f"{str(copia_mes).zfill(2)}/{str(copia_ano)}"

            p = Gastos(cartao=cartao, categoria=categoria, item=item, valor=valor, parcelas=parcela_atual, parcelado=parcelado, data_inicial=data_inicial_formatada, usuario=usuario)
            p.save()

        return HttpResponseRedirect(reverse('criar_gasto'))
    
    if request.method == 'POST':
        ids_para_deletar = request.POST.get('deletar_selecionados', '')
        if ids_para_deletar:
            ids_para_deletar = ids_para_deletar.split(',')
            gastos = Gastos.objects.filter(id__in=ids_para_deletar, usuario=request.user)
            gastos.delete()
            
            return HttpResponseRedirect(reverse('criar_gasto'))

    gastos = Gastos.objects.filter(usuario=request.user)

    #Por cartão
    gastos_por_cartao = defaultdict(Decimal)
    for gasto in gastos:
        gastos_por_cartao[gasto.cartao] += Decimal(gasto.valor_parcelado())

    cartoes = list(gastos_por_cartao.keys())
    valores_totais = [float(valor) for valor in gastos_por_cartao.values()]

    fig_cartao = go.Figure(data=[go.Pie(labels=cartoes, values=valores_totais)])
    fig_cartao.update_traces(
        textinfo="percent",
        hovertemplate="%{label}<br>R$ %{value:,.2f}<br>%{percent}<extra></extra>",
    )
    fig_cartao.update_layout(
        title="Distribuição por cartões",
        width=800,
        height=400,
        paper_bgcolor='rgb(252, 250, 235)',
        plot_bgcolor='white'
    )
    graph_json_cartao = fig_cartao.to_json()

    #Por categoria
    gastos_por_categoria = defaultdict(Decimal)
    for gasto in gastos:
        gastos_por_categoria[gasto.categoria] += Decimal(gasto.valor_parcelado())

    categorias = list(gastos_por_categoria.keys())
    valores_categoria = [float(valor) for valor in gastos_por_categoria.values()]

    fig_categoria = go.Figure(data=[go.Pie(labels=categorias, values=valores_categoria)])
    fig_categoria.update_traces(
        textinfo="percent",
        hovertemplate="%{label}<br>R$ %{value:,.2f}<br>%{percent}<extra></extra>",
    )
    fig_categoria.update_layout(
        title="Distribuição por categorias",
        width=800,
        height=400,
        paper_bgcolor='rgb(252, 250, 235)',
        plot_bgcolor='white'
    )
    graph_json_categoria = fig_categoria.to_json()

    return render(request, "usuarios/usuario.html", {
        "gastos": gastos,
        "graph_json_cartao": graph_json_cartao,
        "graph_json_categoria": graph_json_categoria,
    })


def gastosIndividuais(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    if request.method == 'POST':
        ids_para_deletar = request.POST.get('deletar_selecionados', '')
        if ids_para_deletar:
            ids_para_deletar = ids_para_deletar.split(',')
            gastos = Gastos.objects.filter(id__in=ids_para_deletar, usuario=request.user)
            gastos.delete()
            
            return HttpResponseRedirect(reverse('gastosIndividuais'))

    cartoes = Gastos.objects.filter(usuario=request.user).values_list('cartao', flat=True).distinct()
    cartoes_filtrados = None
    cartoes_filtrados = Gastos.objects.filter(cartao=cartoes[0], usuario=request.user)
    
    if request.method == "POST" and 'buscarCartoes' in request.POST:
        cartao_buscado = request.POST.get("cartao")
        if cartao_buscado:
            cartoes_filtrados = Gastos.objects.filter(cartao=cartao_buscado, usuario=request.user)
    
    
    return render(request, 'usuarios/gastosIndividuais.html', {
        'cartoes': cartoes,
        'gastos': cartoes_filtrados
    })



def gastosMensais(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    datas_disponiveis = Gastos.objects.filter(usuario=request.user).values_list('data_inicial', flat=True).distinct()
    lista_datas = list(datas_disponiveis)
    lista_datas_sort = sorted(lista_datas, key=lambda x: datetime.strptime(x, "%m/%Y"))
    datas_disponiveis_ordenadas = lista_datas_sort
    gastos_filtrados = None
    nenhuma_data = False
    if request.method == 'POST':

        ids_para_deletar = request.POST.get('deletar_selecionados', '')

        if ids_para_deletar:
            ids_para_deletar = ids_para_deletar.split(',')
            
            gastos = Gastos.objects.filter(id__in=ids_para_deletar, usuario=request.user)
            gastos.delete()
            
            return HttpResponseRedirect(reverse('gastosIndividuais'))

    cartoes = Gastos.objects.filter(usuario=request.user).values_list('cartao', flat=True).distinct()
    cartoes_filtrados = None
    agora = datetime.now()
    agora_formatado = agora.strftime("%m/%Y") 
    gastos_filtrados = Gastos.objects.filter(data_inicial=agora_formatado, usuario=request.user)

    if request.method == "POST" and 'consultaMensal' in request.POST:
        consultar_data = request.POST.get("data_inicial_formatada")
        if consultar_data:
            gastos_filtrados = Gastos.objects.filter(data_inicial=consultar_data, usuario=request.user)

    return render(request, "usuarios/gastosMensais.html", {
        "gastos": gastos_filtrados,
        "datas_disponiveis": datas_disponiveis_ordenadas,
    })
    

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return render(request, 'usuarios/login.html', {
                "mensagem": "Cadastro realizado com sucesso!"
            })
        else:
            return render(request, 'usuarios/register.html', {'form': form, 'erro': 'Verifique os dados fornecidos.'})
    else:
        form = UserRegistrationForm()
    return render(request, 'usuarios/register.html', {'form': form})