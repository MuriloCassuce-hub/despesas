from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models import Sum

# Create your models here.

#Tabela de Gastos
class Gastos(models.Model):

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
    
    cartao = models.CharField(max_length=20)
    item = models.CharField(max_length=64)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    parcelas = models.CharField(max_length=6)
    parcelado = models.IntegerField()
    categoria = models.CharField(max_length=30, choices=CATEGORIA_GASTO)
    data_inicial = models.CharField(max_length=5)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
       
    def valor_parcelado(self):
        if self.parcelado > 0:
            valor_parcelado = self.valor/self.parcelado
            return valor_parcelado
        return 0.00
    
    
    def __str__(self):
        return f"{self.usuario.username} {self.cartao} {self.item} {self.categoria} {self.valor} {self.parcelas} {self.parcelado} {self.valor_parcelado():.2f} {self.data_inicial}"

class EntradaDinheiro(models.Model):
    origem = models.CharField(max_length=70)
    valor_de_entrada = models.DecimalField(max_digits=1000000, decimal_places=2)
    DataEntradaSaldo = models.CharField(max_length=7)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def total(self):
        total_entradas = EntradaDinheiro.objects.filter(usuario = self.usuario, DataEntradaSaldo=self.DataEntradaSaldo).aggregate(Sum('valor_de_entrada'))
        return total_entradas['valor_de_entrada__sum']

    def __str__(self):
        return f"{self.usuario.username} {self.valor_de_entrada} {self.DataEntradaSaldo} {self.origem} {self.total()}"

#Tabela de Pessoas
class User(AbstractUser):
    nome = models.CharField(max_length=100)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(unique=True)
    
    def __str__(self):
        return self.username  