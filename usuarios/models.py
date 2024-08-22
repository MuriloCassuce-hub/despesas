from django.db import models

# Create your models here.
class Gastos(models.Model):
    cartao = models.CharField(max_length=20)
    item = models.CharField(max_length=64)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    parcelas = models.IntegerField()

    def valor_parcelado(self):
        if self.parcelas > 0:
            valor_parcelado = self.valor/self.parcelas
            return valor_parcelado
        return 0.00
    
    def __str__(self):
        return f"{self.cartao} {self.item} {self.valor} {self.parcelas} {self.valor_parcelado():.2f}"
