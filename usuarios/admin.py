from django.contrib import admin

from .models import Gastos, User, EntradaDinheiro

# Register your models here.

#Site de administração
admin.site.register(Gastos)
admin.site.register(User)
admin.site.register(EntradaDinheiro)