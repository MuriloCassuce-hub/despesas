from django.urls import path
from . import views


#Views do site (exemplo.com/criar_gasto/)
urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("criar_gasto/", views.criar_gasto, name="criar_gasto"),
    path('gastosIndividuais', views.gastosIndividuais, name="gastosIndividuais"),
    path('register/', views.register, name='register'),

]