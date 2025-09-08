# cotisation_system/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static



# core/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    # Employeurs
    path('employeurs/', views.employeur_list, name='employeur_list'),
    path('employeurs/nouveau/', views.employeur_create, name='employeur_create'),
    path('employeurs/<int:pk>/', views.employeur_detail, name='employeur_detail'),
    path('employeurs/<int:pk>/modifier/', views.employeur_update, name='employeur_update'),
    
    # Assurés
    path('assures/', views.assure_list, name='assure_list'),
    path('assures/nouveau/', views.assure_create, name='assure_create'),
    
    # Déclarations
    path('declarations/', views.declaration_list, name='declaration_list'),
    path('declarations/nouvelle/', views.declaration_create, name='declaration_create'),
    
    # Paiements
    path('paiements/', views.paiement_list, name='paiement_list'),
    path('paiements/nouveau/', views.paiement_create, name='paiement_create'),
    
    # Tableaux de bord
    path('dashboard/', views.dashboard, name='dashboard'),
    path('rapports/', views.rapports, name='rapports'),
    
    # API pour les données
    path('api/kpi-data/', views.kpi_data, name='kpi_data'),
    
 
