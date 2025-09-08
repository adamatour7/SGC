# core/forms.py (mise à jour)
from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'first_name', 'last_name', 'phone']

class EmployeurForm(forms.ModelForm):
    pieces_justificatives = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'multiple': False}),
        label="Pièces justificatives"
    )
    
    class Meta:
        model = Employeur
        fields = ['numero_immatriculation','raison_sociale', 'nif', 'rccm', 'secteur_activite', 'region', 
                 'adresse', 'latitude', 'longitude', 'contact_nom', 'contact_email', 
                 'contact_telephone', 'statut']
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 3}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        
        # Limiter les choix de statut selon le contexte
        if not kwargs.get('instance'):
            self.fields['statut'].initial = 'prospecte'
            


class AssureForm(forms.ModelForm):
    class Meta:
        model = Assure
        fields = ['numero_assure','nom', 'prenom', 'date_naissance', 'lieu_naissance', 'numero_cni',
                 'adresse', 'telephone', 'email', 'type_assure', 'employeur']
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
            'adresse': forms.Textarea(attrs={'rows': 3}),
            'type_assure': forms.Select(attrs={'class': 'form-select'}),
            'employeur': forms.Select(attrs={'class': 'form-select'}),
            
        }

class DeclarationForm(forms.ModelForm):
    class Meta:
        model = Declaration
        fields = ['employeur', 'periode','montant_total_cotisations', 'statut','date_soumission','created_by']
        widgets = {
            'periode': forms.DateInput(attrs={'type': 'date'}),
            'employeur': forms.Select(attrs={'class': 'form-select'}),
            'statut': forms.Select(attrs={'class': 'form-select'}), 
            'date_soumission': forms.DateInput(attrs={'type': 'date'}),
            'created_by': forms.Select(attrs={'class': 'form-select'}),
            
        }

class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ['declaration', 'montant', 'mode_paiement', 'date_paiement', 'preuve_paiement','statut','enregistre_par']
        widgets = {
            'date_paiement': forms.DateInput(attrs={'type': 'date'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-select'}),
            'declaration': forms.Select(attrs={'class': 'form-select'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'enregistre_par': forms.Select(attrs={'class': 'form-select'}),
        }
        
        
class ActionRecouvrementForm(forms.ModelForm):
    class Meta:
        model = ActionRecouvrement
        fields = ['employeur', 'type_action', 'date_planification', 'agent', 'observations']
        widgets = {
            'date_planification': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'observations': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les employeurs qui ont des arriérés
        self.fields['employeur'].queryset = Employeur.objects.filter(
            declarations__paiements__isnull=True
        ).distinct()

class ActionRecouvrementUpdateForm(forms.ModelForm):
    class Meta:
        model = ActionRecouvrement
        fields = ['statut', 'date_execution', 'montant_recouvre', 'observations']
        widgets = {
            'date_execution': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'observations': forms.Textarea(attrs={'rows': 3}),
        }        