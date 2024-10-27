from datetime import datetime

def suprir_meses(lista_de_entrada):
    if not lista_de_entrada:
        return[]
    lista_de_entrada = sorted(set(lista_de_entrada), key=lambda x: datetime.strptime(x, "%m/%Y"))
    primeira_data = datetime.strptime(lista_de_entrada[0], "%m/%Y")
    ultima_data = datetime.strptime(lista_de_entrada[-1], "%m/%Y")
    alinhados = []
    data_atual = primeira_data

    while data_atual <= ultima_data:
        alinhados.append(data_atual.strftime("%m/%Y"))
        if data_atual.month == 12:
            data_atual = data_atual.replace(year=data_atual.year + 1, month=1)
        else:
            data_atual = data_atual.replace(month=data_atual.month + 1)
    
    return alinhados



def corrigir_linha_temporal(lista1completa, lista1, lista2):
    novalista_gastos_data = []
    novalista_gastos_valor = []
    for data in lista1completa:
        if data in lista1:
            idx = lista1.index(data)
            novalista_gastos_data.append(data)
            novalista_gastos_valor.append(lista2[idx])
        else:
            novalista_gastos_data.append(data)
            novalista_gastos_valor.append(0)

    return novalista_gastos_data, novalista_gastos_valor