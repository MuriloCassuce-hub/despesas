from django.urls import path
from . import views
from django.contrib import admin



urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("CriarGastos/", views.criar_gasto, name="criar_gasto"),
    path('GastosPorCartao/', views.gastosIndividuais, name="gastosIndividuais"),
    path('GastosMensais/', views.gastosMensais, name="gastosMensais"),
    path('register/', views.register, name='register'),
    path('AdicionarReceita/', views.AdicionarSaldo, name='AdicionarSaldo'),
    path('ImportarGastos/',views.ImportarGastos, name='ImportarGastos'),
    path('FimDoTeste/', views.FimDoTeste, name='FimDoTeste'),
]