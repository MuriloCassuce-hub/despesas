from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from .models import Gastos, EntradaDinheiro
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.shortcuts import render
from .forms import UserRegistrationForm
import plotly.graph_objects as go
from collections import defaultdict
from decimal import Decimal
from datetime import datetime
from .corrigir_meses import suprir_meses, corrigir_linha_temporal
import pandas as pd
import json
from django.db import IntegrityError

User = get_user_model()

#Verificação index
def index(request):

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    LimiteDadosGastosUsuarios = Gastos.objects.filter(usuario=request.user)
    LimiteDadosGastosUsuarios_list = list(LimiteDadosGastosUsuarios)
    LimiteDadosReceitasUsuarios = EntradaDinheiro.objects.filter(usuario=request.user)
    LimiteDadosReceitasUsuarios_list = list(LimiteDadosReceitasUsuarios)

    if len(LimiteDadosReceitasUsuarios_list) > 150 or len(LimiteDadosGastosUsuarios_list) > 150:
        return HttpResponseRedirect(reverse("FimDoTeste"))
    
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

#Importar Gastos por planilha
def ImportarGastos(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    LimiteDadosGastosUsuarios = Gastos.objects.filter(usuario=request.user)
    LimiteDadosGastosUsuarios_list = list(LimiteDadosGastosUsuarios)
    LimiteDadosReceitasUsuarios = EntradaDinheiro.objects.filter(usuario=request.user)
    LimiteDadosReceitasUsuarios_list = list(LimiteDadosReceitasUsuarios)

    if len(LimiteDadosReceitasUsuarios_list) > 150 or len(LimiteDadosGastosUsuarios_list) > 150:
        return HttpResponseRedirect(reverse("FimDoTeste"))
    
    CATEGORIA_GASTO = [
        ("Alimentação", "Alimentação"),
        ("Transporte", "Transporte"),
        ("Entretenimento", "Entretenimento"),
        ("Moradia", "Moradia"),
        ("Lazer", "Lazer"),
        ("Educação", "Educação"),
        ("Serviços", "Serviços"),
        ("Saúde", "Saúde"),
        ("Outros", "Outros"),
    ]
    
    mensagem = ""

    if request.method == "POST" and "ImportarGasto" in request.POST:
        arquivo = request.FILES.get('arquivoXLSX')
        if not arquivo:
            mensagem = "Nenhum arquivo selecionado."
            return render(request, 'usuarios/ImportarGastos.html', {"mensagem": mensagem})

        try:
            df = pd.read_excel(arquivo)
            df_sem_vazios = df.dropna(subset=['cartao', 'item', 'valor', 'parcelas', 'categoria', 'data_primeira_parcela'])
            num_linhas_sem_vazios = df_sem_vazios.shape[0]
            if num_linhas_sem_vazios > 50:
                mensagem = "Quantidade de dados não permitida para teste. Caso deseje adicionar mais que 50 dados, me contate no linkedin."
                return render(request, 'usuarios/ImportarGastos.html', {"mensagem": mensagem})
            
            if num_linhas_sem_vazios > 10:
                max_parcelas = 20
            else: 
                max_parcelas = 50

            if (df_sem_vazios['parcelas'] > max_parcelas).any():
                mensagem = f"Erro: O campo 'parcelas' contém valores superiores a {max_parcelas} para o número de linhas importadas. Verifique e tente novamente."
                return render(request, 'usuarios/ImportarGastos.html', {"mensagem": mensagem})


            else:
                total_registros = 0
                for i, row in df.iterrows():
                    if all(pd.notnull([row['cartao'], row['item'], row['valor'], row['parcelas'], row['categoria'], row['data_primeira_parcela']])):
                        cartao = row['cartao'].capitalize()
                        item = row['item'].capitalize()
                        valor = row['valor']
                        parcelas = int(row['parcelas'])
                        categoria = row['categoria'].capitalize()
                        data_primeira_parcela = str(row['data_primeira_parcela'])
            
                        categorias_permitidas = [c[0] for c in CATEGORIA_GASTO]
                        if categoria not in categorias_permitidas:
                            mensagem = f"Erro: Categoria '{categoria}' não é válida. Certifique-se que está seguindo o modelo padrão."
                            return render(request, 'usuarios/ImportarGastos.html', {"mensagem": mensagem})

                        try:
                            data_inicial = datetime.strptime(data_primeira_parcela, "%m/%Y")
                        except ValueError:
                            mensagem = f"Erro: Formato de data inválido em {data_primeira_parcela}. Certifique-se que está seguindo o modelo padrão."
                            return render(request, 'usuarios/ImportarGastos.html', {"mensagem": mensagem})

                        copia_mes = data_inicial.month
                        copia_ano = data_inicial.year

                        for i in range(1, parcelas + 1):
                            if total_registros >= 500:
                                mensagem = "Limite de 500 registros atingido. Reduza o número de parcelas ou a quantidade de dados e tente novamente."
                                return render(request, 'usuarios/ImportarGastos.html', {"mensagem": mensagem})
                            parcela_atual = f"{i}/{parcelas}"
                            if i == 1:
                                data_inicial_formatada = f"{str(copia_mes).zfill(2)}/{str(copia_ano)}"
                            else:
                                copia_mes += 1
                                if copia_mes > 12:
                                    copia_mes = 1
                                    copia_ano += 1
                                data_inicial_formatada = f"{str(copia_mes).zfill(2)}/{str(copia_ano)}"

                            p = Gastos.objects.create(
                                cartao=cartao, categoria=categoria, item=item, valor=valor,
                                parcelas=parcela_atual, parcelado=parcelas, 
                                data_inicial=data_inicial_formatada, usuario=request.user
                            )
                            total_registros += 1
            mensagem = 'Arquivo importado com sucesso!'

        except Exception as e:
            mensagem = f"Erro ao ler o arquivo XLSX: {e}. Certifique-se que está seguindo o modelo padrão."
    return render(request, 'usuarios/ImportarGastos.html', {"mensagem": mensagem})


                
#Pagina de criação de gastos
def criar_gasto(request):

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    LimiteDadosGastosUsuarios = Gastos.objects.filter(usuario=request.user)
    LimiteDadosGastosUsuarios_list = list(LimiteDadosGastosUsuarios)
    LimiteDadosReceitasUsuarios = EntradaDinheiro.objects.filter(usuario=request.user)
    LimiteDadosReceitasUsuarios_list = list(LimiteDadosReceitasUsuarios)

    if len(LimiteDadosReceitasUsuarios_list) > 150 or len(LimiteDadosGastosUsuarios_list) > 150:
        return HttpResponseRedirect(reverse("FimDoTeste"))

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

#Gastos individuais
def gastosIndividuais(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    LimiteDadosGastosUsuarios = Gastos.objects.filter(usuario=request.user)
    LimiteDadosGastosUsuarios_list = list(LimiteDadosGastosUsuarios)
    LimiteDadosReceitasUsuarios = EntradaDinheiro.objects.filter(usuario=request.user)
    LimiteDadosReceitasUsuarios_list = list(LimiteDadosReceitasUsuarios)

    if len(LimiteDadosReceitasUsuarios_list) > 150 or len(LimiteDadosGastosUsuarios_list) > 150:
        return HttpResponseRedirect(reverse("FimDoTeste"))
    
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

def FimDoTeste(request):
    return render(request, 'usuarios/Fimdoteste.html')

def gastosMensais(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    LimiteDadosGastosUsuarios = Gastos.objects.filter(usuario=request.user)
    LimiteDadosGastosUsuarios_list = list(LimiteDadosGastosUsuarios)
    LimiteDadosReceitasUsuarios = EntradaDinheiro.objects.filter(usuario=request.user)
    LimiteDadosReceitasUsuarios_list = list(LimiteDadosReceitasUsuarios)

    if len(LimiteDadosReceitasUsuarios_list) > 150 or len(LimiteDadosGastosUsuarios_list) > 150:
        return HttpResponseRedirect(reverse("FimDoTeste"))
    
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
            existencia = 1
            total_receita = sum(entrada.valor_de_entrada for entrada in datas_filtradas)

        if gastos_filtrados.exists():
                total_entrada = sum(gasto.valor_parcelado() for gasto in gastos_filtrados)
                datas_filtradas = EntradaDinheiro.objects.filter(DataEntradaSaldo=consultar_data, usuario=request.user)
                total_saldo = sum(entrada.valor_de_entrada for entrada in datas_filtradas)
                total_saldo = total_saldo - total_entrada
                existencia = 1
                total_receita = sum(entrada.valor_de_entrada for entrada in datas_filtradas)
        else:
            total_entrada = 0
            total_saldo = 0
            existencia = 0
            total_receita = 0

    else:
        verifica = Gastos.objects.filter(usuario = request.user).values_list('data_inicial', flat=True).distinct()
        if not gastos_filtrados.exists():
            total_entrada = 0
            total_saldo = 0
            existencia = 0
            total_receita = 0
        elif agora_formatado not in verifica:
            primeira_data = Gastos.objects.filter(usuario = request.user).values_list('data_inicial', flat=True).distinct()
            consultar_data = primeira_data[0]
            datas_filtradas = EntradaDinheiro.objects.filter(DataEntradaSaldo=consultar_data, usuario=request.user)
            gastos_filtrados = Gastos.objects.filter(data_inicial=consultar_data, usuario=request.user)
            existencia = 1
            total_receita = sum(entrada.valor_de_entrada for entrada in datas_filtradas)
    
            total_entrada = sum(gasto.valor_parcelado() for gasto in gastos_filtrados)
            datas_filtradas = EntradaDinheiro.objects.filter(DataEntradaSaldo=consultar_data, usuario=request.user)
            total_saldo = sum(entrada.valor_de_entrada for entrada in datas_filtradas) - total_entrada
        else:
            gastos_filtrados = Gastos.objects.filter(data_inicial=agora_formatado, usuario=request.user)
            total_entrada = sum(gasto.valor_parcelado() for gasto in gastos_filtrados)
            datas_filtradas = EntradaDinheiro.objects.filter(DataEntradaSaldo=agora_formatado, usuario=request.user)
            total_saldo = sum(entrada.valor_de_entrada for entrada in datas_filtradas) - total_entrada
            total_receita = sum(entrada.valor_de_entrada for entrada in datas_filtradas)
            existencia = 1



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
    filtrar_anos = Gastos.objects.filter(usuario=request.user).values_list("data_inicial", flat=True).distinct()
    anos_distintos = sorted(list({data.split("/")[1] for data in filtrar_anos}))
    #Gastos
    gastos_totais_mensal = Gastos.objects.filter(usuario=request.user).values_list("data_inicial", flat=True).distinct()
    tratando = list(gastos_totais_mensal)
    gastos_totais_mensal = sorted(tratando, key=lambda x: datetime.strptime(x, "%m/%Y"))
    lista_valor_gastos = []
    lista_data_gastos = []
    for data in gastos_totais_mensal:
        data_datetime = datetime.strptime(data, "%m/%Y")
        gastos_do_mes = Gastos.objects.filter(usuario=request.user, data_inicial=data)
        total_mes = sum(gasto.valor_parcelado() for gasto in gastos_do_mes)
        lista_valor_gastos.append(total_mes)
        mes_ano = data_datetime.strftime("%m/%Y")
        lista_data_gastos.append(mes_ano)
    
    nova_lista_datas = suprir_meses(lista_data_gastos)
    lista_data_gastos, lista_valor_gastos = corrigir_linha_temporal(nova_lista_datas, lista_data_gastos, lista_valor_gastos)
    
    #Receita
    saldos_totais_mensal = EntradaDinheiro.objects.filter(usuario=request.user).values_list("DataEntradaSaldo", flat=True).distinct()
    lista_valor_receita = []
    lista_meses_receita = []

    for data in saldos_totais_mensal:
        data_datetime = datetime.strptime(data, "%m/%Y")
        saldos_do_mes = EntradaDinheiro.objects.filter(usuario=request.user, DataEntradaSaldo=data)
        total_saldo_mes = sum(entrada.valor_de_entrada for entrada in saldos_do_mes)
        lista_valor_receita.append(total_saldo_mes)
        mes_ano = data_datetime.strftime("%m/%Y")
        lista_meses_receita.append(mes_ano)

    nova_lista_datas_receita = suprir_meses(lista_meses_receita)
    lista_meses_receita, lista_valor_receita = corrigir_linha_temporal(nova_lista_datas_receita, lista_meses_receita, lista_valor_receita)
    
    saldos_unicos = set(lista_meses_receita)
    gastos_unicos = set(lista_data_gastos)
    for mes in saldos_unicos:
        if mes not in gastos_unicos:
            lista_data_gastos.append(mes)
            lista_data_gastos = sorted(lista_data_gastos, key=lambda x: datetime.strptime(x, "%m/%Y"))
            pos = lista_data_gastos.index(mes)
            lista_valor_gastos.insert(pos, 0)
    saldos_alinhados = []
    for mes in lista_data_gastos:
        if mes in lista_meses_receita:
            index = lista_meses_receita.index(mes)
            saldos_alinhados.append(lista_valor_receita[index])
        else:
            saldos_alinhados.append(0)

    cores_saldos = []
    saldo = []
    for i in range(len(saldos_alinhados)):
        diferenca = saldos_alinhados[i] - lista_valor_gastos[i]
        saldo.append(diferenca)
        if diferenca < 0:
            cores_saldos.append('red')
        else:
            cores_saldos.append('green')

    fig_mensal = go.Figure()
    fig_mensal.add_trace(go.Scatter(
        x=lista_data_gastos,
        y=saldo,
        mode="lines+markers",
        name="Saldo Mensal",
        line=dict(color='blue', width=2),
        marker=dict(size=8, symbol='square', color='blue'),
        hovertemplate="Mês: %{x}<br> Saldo total: R$ %{y:,.2f}<extra></extra>"
    ))
    fig_mensal.add_trace(go.Scatter(
        x=lista_data_gastos,  
        y=lista_valor_gastos,  
        mode='lines+markers',
        name='Gasto Mensal',
        line=dict(color='firebrick', width=2),
        marker=dict(size=8, symbol='circle', color='firebrick'),
        hovertemplate="Mês: %{x}<br>Total de Gastos: R$ %{y:,.2f}<extra></extra>",
    ))
    fig_mensal.add_trace(go.Scatter(
        x=lista_data_gastos,  
        y=saldos_alinhados,  
        mode='lines+markers',
        name='Receita Mensal',
        line=dict(color='green', width=2),
        marker=dict(size=8, symbol='circle', color='green'),
        hovertemplate="Mês: %{x}<br>Receita total: R$ %{y:,.2f}<extra></extra>",
    ))
    if existencia == 1:
        fig_mensal.update_layout(
            title={'text': "Gastos e Receitas Mensais", 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'rgb(19, 75, 112)', 'size':24}},
            yaxis_title="Total em R$",
            width=900,
            height=500,
            paper_bgcolor='rgb(252, 250, 235)',
            plot_bgcolor='rgb(252, 250, 235)',
            hovermode='x',
            xaxis=dict(
                tickmode='array',
                tickvals=lista_data_gastos,  
                ticktext=lista_data_gastos,  
            ),
            shapes=[{'type': 'line', 'x0': min(lista_data_gastos), 'y0': 0, 'x1': max(lista_data_gastos), 'y1': 0, 'line': {'color': 'black', 'width': 2, 'dash': 'solid'}}],
        )
    else:
        fig_mensal.update_layout(
            title={'text': "Gastos e Receitas Mensais", 'x': 0.5, 'xanchor': 'center', 'font': {'color': 'rgb(19, 75, 112)', 'size':24}},
            yaxis_title="Total em R$",
            width=900,
            height=500,
            paper_bgcolor='rgb(252, 250, 235)',
            plot_bgcolor='rgb(252, 250, 235)',
            hovermode='x',
            xaxis=dict(
                tickmode='array',
                tickvals=lista_data_gastos,  
                ticktext=lista_data_gastos,  
            ),
        )
    graph_json_mensal = fig_mensal.to_json()
    
    exportar_todos_gastos = Gastos.objects.filter(usuario=request.user).values()
    exportar_todos_gastos_list = list(exportar_todos_gastos)

    usuario = request.user

    for gasto in exportar_todos_gastos_list:
        gasto['valor'] = float(gasto['valor'])

    if request.GET.get('download') == 'json':
        response = HttpResponse(
            json.dumps(exportar_todos_gastos_list, ensure_ascii=False, indent=4),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="Gastos.{usuario}.json"'
        return response


    return render(request, "usuarios/gastosMensais.html", {
        "gastos": gastos_filtrados,
        "datas_disponiveis": datas_disponiveis_ordenadas,
        "total_entrada": total_entrada,
        "total_saldo": total_saldo,
        "graph_json_cartao": graph_json_cartao,
        "graph_json_categoria": graph_json_categoria,
        "graph_json_mensal": graph_json_mensal,
        "anos_distintos": anos_distintos,
        "existencia": existencia,
        "total_receita": total_receita,
        "importar_todos_gastos_list": exportar_todos_gastos_list,
    })

def AdicionarSaldo(request):

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    LimiteDadosGastosUsuarios = Gastos.objects.filter(usuario=request.user)
    LimiteDadosGastosUsuarios_list = list(LimiteDadosGastosUsuarios)
    LimiteDadosReceitasUsuarios = EntradaDinheiro.objects.filter(usuario=request.user)
    LimiteDadosReceitasUsuarios_list = list(LimiteDadosReceitasUsuarios)

    if len(LimiteDadosReceitasUsuarios_list) > 150 or len(LimiteDadosGastosUsuarios_list) > 150:
        return HttpResponseRedirect(reverse("FimDoTeste"))

    exportar_todas_receitas = EntradaDinheiro.objects.filter(usuario=request.user).values()
    exportar_todas_receitas_list = list(exportar_todas_receitas)
    usuario = request.user

    for receita in exportar_todas_receitas_list:
        receita['valor_de_entrada'] = float(receita['valor_de_entrada'])

    if request.GET.get('download') == 'json':
        response = HttpResponse(
            json.dumps(exportar_todas_receitas_list, ensure_ascii=False, indent=4),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="Receitas.{usuario}.json"'
        return response
    
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
        "importar_todos_gastos_list": exportar_todas_receitas_list,
    })

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exists():
                return render(request, 'usuarios/register.html', {
                    'form': form,
                    'erro': 'Este email já está em uso.'
                })
            try:
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.save()
                return render(request, 'usuarios/login.html', {
                    "mensagem": "Cadastro realizado com sucesso!"
                })
            except IntegrityError:
                return render(request, 'usuarios/register.html', {
                    'form': form,
                    'erro': 'Esse email já está registrado.'
                })
        else:
            return render(request, 'usuarios/register.html', {
                'form': form,
                'erro': 'Verifique os dados fornecidos.'
            })
    else:
        form = UserRegistrationForm()
    return render(request, 'usuarios/register.html', {'form': form})