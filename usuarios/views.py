from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Gastos, EntradaDinheiro
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
    
    return HttpResponseRedirect(reverse("gastosMensais"))

#Página de login
def login_view(request):

    if request.method=="POST":
        usuario = request.POST.get("usuario")
        senha = request.POST.get("senha")
        usuario = authenticate(request, username = usuario, password = senha)
        if usuario is not None:
            login(request, usuario)
            return HttpResponseRedirect(reverse("gastosMensais"))
        
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
        title={'text': "Distribuição total por cartões", 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'rgb(19, 75, 112)', 'size':24}},
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
        title={'text': "Distribuição total por categoria", 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'rgb(19, 75, 112)', 'size':24}},
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
    total_entrada = 0

    
    if Gastos.objects.filter(usuario=request.user).exists():
        cartoes_filtrados = Gastos.objects.filter(cartao=cartoes[0], usuario=request.user)
    
    if request.method == "POST" and 'buscarCartoes' in request.POST:
        cartao_buscado = request.POST.get("cartao")
        if cartao_buscado:
            cartoes_filtrados = Gastos.objects.filter(cartao=cartao_buscado, usuario=request.user)
    
    if cartoes_filtrados != None:
        total_entrada = sum(gasto.valor_parcelado() for gasto in cartoes_filtrados)

    return render(request, 'usuarios/gastosIndividuais.html', {
        'cartoes': cartoes,
        'gastos': cartoes_filtrados,
        'total_entrada': total_entrada,
    })



def gastosMensais(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    datas_disponiveis = Gastos.objects.filter(usuario=request.user).values_list('data_inicial', flat=True).distinct()
    lista_datas = list(datas_disponiveis)
    lista_datas_sort = sorted(lista_datas, key=lambda x: datetime.strptime(x, "%m/%Y"))
    datas_disponiveis_ordenadas = lista_datas_sort
    if request.method == 'POST':

        ids_para_deletar = request.POST.get('deletar_selecionados', '')

        if ids_para_deletar:
            ids_para_deletar = ids_para_deletar.split(',')
            
            gastos = Gastos.objects.filter(id__in=ids_para_deletar, usuario=request.user)
            gastos.delete()
            
            return HttpResponseRedirect(reverse('gastosMensais'))

    cartoes = Gastos.objects.filter(usuario=request.user).values_list('cartao', flat=True).distinct()
    agora = datetime.now()
    agora_formatado = agora.strftime("%m/%Y") 
    gastos_filtrados = Gastos.objects.filter(usuario=request.user)
    
    if request.method == "POST" and 'consultaMensal' in request.POST:
        consultar_data = request.POST.get("data_inicial_formatada")
        if consultar_data:
            gastos_filtrados = Gastos.objects.filter(data_inicial=consultar_data, usuario=request.user)

        if gastos_filtrados.exists():
                total_entrada = sum(gasto.valor_parcelado() for gasto in gastos_filtrados)
                datas_filtradas = EntradaDinheiro.objects.filter(DataEntradaSaldo=consultar_data, usuario=request.user)
                total_saldo = sum(entrada.valor_de_entrada for entrada in datas_filtradas)
                total_saldo = total_saldo - total_entrada
        else:
            total_entrada = 0
            total_saldo = 0

    else:
        verifica = Gastos.objects.filter(usuario = request.user).values_list('data_inicial', flat=True).distinct()
        if not gastos_filtrados.exists():
            total_entrada = 0
            total_saldo = 0
        elif agora_formatado not in verifica:
            primeira_data = Gastos.objects.filter(usuario = request.user).values_list('data_inicial', flat=True).distinct()
            consultar_data = primeira_data[0]
            gastos_filtrados = Gastos.objects.filter(data_inicial=consultar_data, usuario=request.user)
    
            total_entrada = sum(gasto.valor_parcelado() for gasto in gastos_filtrados)
            datas_filtradas = EntradaDinheiro.objects.filter(DataEntradaSaldo=consultar_data, usuario=request.user)
            total_saldo = sum(entrada.valor_de_entrada for entrada in datas_filtradas) - total_entrada
        else:
            gastos_filtrados = Gastos.objects.filter(data_inicial=agora_formatado, usuario=request.user)
            total_entrada = sum(gasto.valor_parcelado() for gasto in gastos_filtrados)
            datas_filtradas = EntradaDinheiro.objects.filter(DataEntradaSaldo=agora_formatado, usuario=request.user)
            total_saldo = sum(entrada.valor_de_entrada for entrada in datas_filtradas) - total_entrada




    #Por cartão
    gastos_por_cartao = defaultdict(Decimal)
    for gasto in gastos_filtrados:
        gastos_por_cartao[gasto.cartao] += Decimal(gasto.valor_parcelado())

    cartoes = list(gastos_por_cartao.keys())
    valores_totais = [float(valor) for valor in gastos_por_cartao.values()]

    fig_cartao = go.Figure(data=[go.Pie(labels=cartoes, values=valores_totais)])
    fig_cartao.update_traces(
        textinfo="percent",
        hovertemplate="%{label}<br>R$ %{value:,.2f}<br>%{percent}<extra></extra>",
    )
    fig_cartao.update_layout(
        title={'text': "Distribuição por cartões", 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'rgb(19, 75, 112)', 'size':24}},
        width=800,
        height=400,
        paper_bgcolor='rgb(252, 250, 235)',
        plot_bgcolor='white'
    )
    graph_json_cartao = fig_cartao.to_json()

    #Por categoria
    gastos_por_categoria = defaultdict(Decimal)
    for gasto in gastos_filtrados:
        gastos_por_categoria[gasto.categoria] += Decimal(gasto.valor_parcelado())

    categorias = list(gastos_por_categoria.keys())
    valores_categoria = [float(valor) for valor in gastos_por_categoria.values()]

    fig_categoria = go.Figure(data=[go.Pie(labels=categorias, values=valores_categoria)])
    fig_categoria.update_traces(
        textinfo="percent",
        hovertemplate="%{label}<br>R$ %{value:,.2f}<br>%{percent}<extra></extra>",
    )
    fig_categoria.update_layout(
        title={'text': "Distribuição por categoria", 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'rgb(19, 75, 112)', 'size':24}},
        width=800,
        height=400,
        paper_bgcolor='rgb(252, 250, 235)',
        plot_bgcolor='white'
    )
    graph_json_categoria = fig_categoria.to_json()


    #Por linhas mensais

    #Gastos
    gastos_totais_mensal = Gastos.objects.filter(usuario=request.user).values_list("data_inicial", flat=True).distinct()
    lista1 = []
    lista2 = []
    for data in gastos_totais_mensal:
        data_datetime = datetime.strptime(data, "%m/%Y")
        gastos_do_mes = Gastos.objects.filter(usuario=request.user, data_inicial=data)
        total_mes = sum(gasto.valor_parcelado() for gasto in gastos_do_mes)
        lista1.append(total_mes)
        mes_ano = data_datetime.strftime("%m/%Y")
        lista2.append(mes_ano)

    #Saldo
    saldos_totais_mensal = EntradaDinheiro.objects.filter(usuario=request.user).values_list("DataEntradaSaldo", flat=True).distinct()
    lista3 = []
    lista4 = []

    for data in saldos_totais_mensal:
        data_datetime = datetime.strptime(data, "%m/%Y")
        saldos_do_mes = EntradaDinheiro.objects.filter(usuario=request.user, DataEntradaSaldo=data)
        total_saldo_mes = sum(entrada.valor_de_entrada for entrada in saldos_do_mes)
        lista3.append(total_saldo_mes)
        mes_ano = data_datetime.strftime("%m/%Y")
        lista4.append(mes_ano)

    saldos_unicos = set(lista4)
    gastos_unicos = set(lista2)
    for mes in saldos_unicos:
        if mes not in gastos_unicos:
            lista2.append(mes)
            lista1.append(0)
    saldos_alinhados = []
    for mes in lista2:
        if mes in lista4:
            index = lista4.index(mes)
            saldos_alinhados.append(lista3[index])
        else:
            saldos_alinhados.append(0)

    fig_mensal = go.Figure()
    fig_mensal.add_trace(go.Scatter(
        x=lista2,  
        y=lista1,  
        mode='lines+markers',
        name='Gastos Mensais',
        line=dict(color='firebrick', width=2),
        marker=dict(size=8, symbol='circle', color='firebrick'),
        hovertemplate="Mês: %{x}<br>Total de Gastos: R$ %{y:,.2f}<extra></extra>",
    ))
    fig_mensal.add_trace(go.Scatter(
        x=lista2,  
        y=saldos_alinhados,  
        mode='lines+markers',
        name='Saldos Mensais',
        line=dict(color='green', width=2),
        marker=dict(size=8, symbol='circle', color='green'),
        hovertemplate="Mês: %{x}<br>Total de Saldos: R$ %{y:,.2f}<extra></extra>",
    ))
    fig_mensal.update_layout(
        title={'text': "Gastos e Saldos Mensais", 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'rgb(19, 75, 112)', 'size':24}},
        xaxis_title="Meses",
        yaxis_title="Total em R$",
        width=800,
        height=400,
        paper_bgcolor='rgb(252, 250, 235)',
        plot_bgcolor='white',
        hovermode='x',
        xaxis=dict(
            tickmode='array',
            tickvals=lista2,  
            ticktext=lista2,  
        ),
    )
    graph_json_mensal = fig_mensal.to_json()

    return render(request, "usuarios/gastosMensais.html", {
        "gastos": gastos_filtrados,
        "datas_disponiveis": datas_disponiveis_ordenadas,
        "total_entrada": total_entrada,
        "total_saldo": total_saldo,
        "graph_json_cartao": graph_json_cartao,
        "graph_json_categoria": graph_json_categoria,
        "graph_json_mensal": graph_json_mensal,
    })

def AdicionarSaldo(request):

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    if request.method == 'POST':

        ids_para_deletar = request.POST.get('deletar_selecionados', '')

        if ids_para_deletar:
            ids_para_deletar = ids_para_deletar.split(',')
            
            excluirSaldo = EntradaDinheiro.objects.filter(id__in=ids_para_deletar, usuario=request.user)
            excluirSaldo.delete()
            
            return HttpResponseRedirect(reverse('AdicionarSaldo'))

    if request.method == 'POST' and 'AdicionarSaldo' in request.POST:
        saldo = request.POST.get("saldo")
        data_de_entrada_saldo = request.POST.get("DataEntradaSaldo")
        origem = request.POST.get("Origem").capitalize()
        copia_mes =  data_de_entrada_saldo[5:7]
        copia_ano = data_de_entrada_saldo[0:4]
        data_de_entrada_saldo = str(copia_mes) + "/" + str(copia_ano)

        if EntradaDinheiro.objects.filter(usuario=request.user, origem=origem, DataEntradaSaldo=data_de_entrada_saldo).exists():
            entrada = EntradaDinheiro.objects.get(usuario=request.user, origem=origem, DataEntradaSaldo=data_de_entrada_saldo)
            entrada.origem = origem
            entrada.valor_de_entrada += Decimal(saldo)
            entrada.save()
            return HttpResponseRedirect(reverse('AdicionarSaldo'))
        else:
            EntradaDinheiro.objects.create(usuario=request.user, origem = origem, valor_de_entrada=Decimal(saldo), DataEntradaSaldo=data_de_entrada_saldo)
            return HttpResponseRedirect(reverse('AdicionarSaldo'))    
    
    datas_disponiveis = EntradaDinheiro.objects.filter(usuario=request.user).values_list('DataEntradaSaldo', flat=True).distinct()
    lista_datas = list(datas_disponiveis)
    lista_datas_sort = sorted(lista_datas, key=lambda x: datetime.strptime(x, "%m/%Y"))
    datas_disponiveis_ordenadas = lista_datas_sort
    
    if datas_disponiveis.exists():
        agora = datetime.now()
        agora_formatado = agora.strftime("%m/%Y") 
        datas_filtradas = EntradaDinheiro.objects.filter(DataEntradaSaldo=agora_formatado, usuario=request.user)
        primeiro_mes = EntradaDinheiro.objects.filter(usuario = request.user).values_list('DataEntradaSaldo', flat=True).distinct()
        if agora_formatado not in datas_disponiveis:
            datas_filtradas = EntradaDinheiro.objects.filter(DataEntradaSaldo=primeiro_mes[0], usuario=request.user)
        total_entrada = sum(entrada.valor_de_entrada for entrada in datas_filtradas)
    else:
        datas_filtradas = EntradaDinheiro.objects.none()
        total_entrada = 0


    
    if request.method == "POST" and 'consultaMensal' in request.POST:
        consultar_data = request.POST.get("data_inicial_formatada")
        if consultar_data:
            datas_filtradas = EntradaDinheiro.objects.filter(DataEntradaSaldo=consultar_data, usuario=request.user)
            total_entrada = sum(entrada.valor_de_entrada for entrada in datas_filtradas)
        else:
            consultar_data = agora_formatado
    return render(request, "usuarios/AdicionarSaldo.html", {
        "entradadinheiro": datas_filtradas,
        "datas_disponiveis": datas_disponiveis_ordenadas,
        "total_entrada": total_entrada,
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