# core/views.py (ajouter cette fonction)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from .models import *
from .forms import *
from django.http import HttpResponse
from django.db.models.functions import TruncMonth

from calendar import month_name
from django.utils.timezone import now

def is_admin(user):
    return user.role == 'admin'

def is_superviseur(user):
    return user.role == 'superviseur'

@login_required
def employeur_update(request, pk):
    employeur = get_object_or_404(Employeur, pk=pk)
    
    # Vérifier les permissions
    if not (request.user.role in ['admin', 'superviseur', 'validation'] and 
            request.user != employeur.agent):
        messages.error(request, "Vous n'avez pas la permission de modifier cet employeur.")
        return redirect('employeur_list')
    
    if request.method == 'POST':
        form = EmployeurForm(request.POST, request.FILES, instance=employeur)
        if form.is_valid():
            employeur = form.save()
            
            # Gérer les pièces justificatives
            pieces = request.FILES.getlist('pieces_justificatives')
            for piece in pieces:
                PieceJustificative.objects.create(
                    employeur=employeur,
                    nom=piece.name,
                    fichier=piece
                )
            
            messages.success(request, 'Employeur modifié avec succès!')
            return redirect('employeur_detail', pk=employeur.pk)
    else:
        form = EmployeurForm(instance=employeur)
    
    return render(request, 'employeur_form.html', {
        'form': form,
        'employeur': employeur,
        'edition': True
    })

@login_required
def employeur_list(request):
    employeurs = Employeur.objects.all().order_by('-date_creation')
    return render(request, 'employeur_list.html', {'employeurs': employeurs})

@login_required
def employeur_create(request):
    if request.method == 'POST':
        form = EmployeurForm(request.POST, request.FILES)
        if form.is_valid():
            employeur = form.save(commit=False)
            employeur.agent = request.user
            employeur.save()
            
            # Gérer les pièces justificatives
            pieces = request.FILES.getlist('pieces_justificatives')
            for piece in pieces:
                PieceJustificative.objects.create(
                    employeur=employeur,
                    nom=piece.name,
                    fichier=piece
                )
            
            messages.success(request, 'Employeur créé avec succès!')
            return redirect('employeur_list')
    else:
        form = EmployeurForm()
    return render(request, 'employeur_form.html', {'form': form})

@login_required
def employeur_detail(request, pk):
    employeur = get_object_or_404(Employeur, pk=pk)
    pieces = employeur.pieces_justificatives.all()
    return render(request, 'employeur_detail.html', {
        'employeur': employeur,
        'pieces': pieces
    })

@login_required
def assure_list(request):
    assures = Assure.objects.all().order_by('-date_affiliation')
    return render(request, 'assure_list.html', {'assures': assures})

@login_required
def assure_create(request):
    if request.method == 'POST':
        form = AssureForm(request.POST)
        if form.is_valid():
            assure = form.save()
            messages.success(request, 'Assuré créé avec succès!')
            return redirect('assure_list')
    else:
        form = AssureForm()
    return render(request, 'assure_form.html', {'form': form})

@login_required
def declaration_list(request):
    declarations = Declaration.objects.all().order_by('-created_at')
    return render(request, 'declaration_list.html', {'declarations': declarations})

@login_required
def declaration_create(request):
    if request.method == 'POST':
        form = DeclarationForm(request.POST)
        if form.is_valid():
            declaration = form.save(commit=False)
            declaration.created_by = request.user
            declaration.save()
            messages.success(request, 'Déclaration créée avec succès!')
            return redirect('declaration_list')
    else:
        form = DeclarationForm()
    return render(request, 'declaration_form.html', {'form': form})

@login_required
def paiement_list(request):
    paiements = Paiement.objects.all().order_by('-date_reception')
    return render(request, 'paiement_list.html', {'paiements': paiements})

@login_required
def paiement_create(request):
    if request.method == 'POST':
        form = PaiementForm(request.POST, request.FILES)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.enregistre_par = request.user
            paiement.reference = f"PAY{timezone.now().strftime('%Y%m%d%H%M%S')}"
            paiement.save()
            messages.success(request, 'Paiement enregistré avec succès!')
            return redirect('paiement_list')
    else:
        form = PaiementForm()
    return render(request, 'paiement_form.html', {'form': form})

# @login_required
def dashboard(request):
    # Calcul des KPI
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # KPI d'extension
    nouveaux_employeurs = Employeur.objects.filter(
        date_creation__date__gte=month_start,
        statut='valide'
    ).count()
    
    nouveaux_assures = Assure.objects.filter(
        date_affiliation__date__gte=month_start
    ).count()
    
    # KPI de conformité
    employeurs_actifs = Employeur.objects.filter(statut='valide').count()
    employeurs_ayant_declare = Declaration.objects.filter(
        periode__month=today.month,
        periode__year=today.year,
        statut='valide'
    ).values('employeur').distinct().count()
    
    taux_conformite = (employeurs_ayant_declare / employeurs_actifs * 100) if employeurs_actifs > 0 else 0
    
    # KPI de recouvrement
    cotisations_declarees = Declaration.objects.filter(
        periode__month=today.month,
        periode__year=today.year,
        statut='valide'
    ).aggregate(total=Sum('montant_total_cotisations'))['total'] or 0
    
    cotisations_encaissees = Paiement.objects.filter(
        declaration__periode__month=today.month,
        declaration__periode__year=today.year,
        statut='confirme'
    ).aggregate(total=Sum('montant'))['total'] or 0
    
    taux_recouvrement = (cotisations_encaissees / cotisations_declarees * 100) if cotisations_declarees > 0 else 0
    
    # Derniers employeurs
    derniers_employeurs = Employeur.objects.filter(statut='valide').order_by('-date_creation')[:5]
    
    # Derniers paiements
    derniers_paiements = Paiement.objects.filter(statut='confirme').order_by('-date_reception')[:5]
    
    
    
    context = {
        'nouveaux_employeurs': nouveaux_employeurs,
        'nouveaux_assures': nouveaux_assures,
        'taux_conformite': round(taux_conformite, 2),
        'taux_recouvrement': round(taux_recouvrement, 2),
        'cotisations_encaissees': cotisations_encaissees,
        'derniers_employeurs': derniers_employeurs,
        'derniers_paiements': derniers_paiements,

    }
    # Vérification avec print()
    print("=== DEBUG DASHBOARD ===")
    print("Cotisations encaissées :", cotisations_encaissees)
    print("Taux de conformité :", taux_conformite)
    print("Taux de recouvrement :", taux_recouvrement)
    print("=======================")

    
    return render(request, 'dashboard.html', context)


# @login_required
# @user_passes_test(is_admin)
def rapports(request):
    return render(request, 'rapports.html')

# @login_required
def kpi_data(request):
    # Données pour les graphiques (exemple simplifié)
    data = {
        'kpi_extension': {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'employeurs': [12, 19, 8, 15, 22, 18],
            'assures': [45, 52, 38, 61, 75, 68]
        },
        'kpi_conformite': {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'taux': [78, 82, 75, 88, 85, 90]
        }
    }
    return JsonResponse(data)




# core/views.py (ajouts)
@login_required
def action_recouvrement_list(request):
    actions = ActionRecouvrement.objects.all().order_by('-date_planification')
    
    # Filtres
    statut_filter = request.GET.get('statut')
    type_filter = request.GET.get('type')
    
    if statut_filter:
        actions = actions.filter(statut=statut_filter)
    if type_filter:
        actions = actions.filter(type_action=type_filter)
    
    return render(request, 'action_recouvrement_list.html', {
        'actions': actions,
        'statut_filter': statut_filter,
        'type_filter': type_filter
    })

@login_required
def action_recouvrement_create(request):
    if request.method == 'POST':
        form = ActionRecouvrementForm(request.POST)
        if form.is_valid():
            action = form.save(commit=False)
            action.created_by = request.user
            action.save()
            messages.success(request, 'Action de recouvrement créée avec succès!')
            return redirect('action_recouvrement_list')
    else:
        form = ActionRecouvrementForm(initial={'agent': request.user})
    
    return render(request, 'action_recouvrement_form.html', {'form': form})

@login_required
def action_recouvrement_detail(request, pk):
    action = get_object_or_404(ActionRecouvrement, pk=pk)
    return render(request, 'action_recouvrement_detail.html', {'action': action})

@login_required
def action_recouvrement_update(request, pk):
    action = get_object_or_404(ActionRecouvrement, pk=pk)
    
    if request.method == 'POST':
        form = ActionRecouvrementUpdateForm(request.POST, instance=action)
        if form.is_valid():
            form.save()
            messages.success(request, 'Action de recouvrement mise à jour avec succès!')
            return redirect('action_recouvrement_detail', pk=action.pk)
    else:
        form = ActionRecouvrementUpdateForm(instance=action)
    
    return render(request, 'action_recouvrement_update.html', {
        'form': form,
        'action': action
    })

@login_required
def action_recouvrement_delete(request, pk):
    action = get_object_or_404(ActionRecouvrement, pk=pk)
    
    if request.method == 'POST':
        action.delete()
        messages.success(request, 'Action de recouvrement supprimée avec succès!')
        return redirect('action_recouvrement_list')
    
    return render(request, 'action_recouvrement_confirm_delete.html', {'action': action})

@login_required
def employeurs_arrieres(request):
    # Employeurs avec des déclarations non payées
    employeurs_arrieres = Employeur.objects.filter(
        declarations__paiements__isnull=True,
        statut='valide'
    ).distinct().annotate(
        montant_du=Sum('declarations__montant_total_cotisations')
    )
    
    return render(request, 'employeurs_arrieres.html', {
        'employeurs_arrieres': employeurs_arrieres
    })