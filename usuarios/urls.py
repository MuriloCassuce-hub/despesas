from django.urls import path
from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("criar_gasto/", views.criar_gasto, name="criar_gasto"),
    path('gastosIndividuais/', views.gastosIndividuais, name="gastosIndividuais"),
    path('gastosMensais', views.gastosMensais, name="gastosMensais"),
    path('register/', views.register, name='register'),
    path('AdicionarSaldo/', views.AdicionarSaldo, name='AdicionarSaldo'),
    path('ImportarGastos/',views.ImportarGastos, name='ImportarGastos'),
]