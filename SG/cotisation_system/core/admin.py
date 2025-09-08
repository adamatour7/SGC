from django.contrib import admin

# Register your models here.
# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {'fields': ('role', 'phone')}),
    )

@admin.register(Employeur)
class EmployeurAdmin(admin.ModelAdmin):
    list_display = ['numero_immatriculation', 'raison_sociale', 'nif', 'secteur_activite', 'statut']
    list_filter = ['statut', 'secteur_activite', 'region']
    search_fields = ['raison_sociale', 'nif', 'rccm']

@admin.register(Assure)
class AssureAdmin(admin.ModelAdmin):
    list_display = ['numero_assure', 'nom', 'prenom', 'type_assure', 'employeur', 'est_actif']
    list_filter = ['type_assure', 'est_actif']
    search_fields = ['nom', 'prenom', 'numero_cni']

admin.site.register(SecteurActivite)
admin.site.register(Region)
admin.site.register(Declaration)
admin.site.register(Paiement)
admin.site.register(ActionRecouvrement)