
# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('agent', 'Agent de Terrain'),
        ('superviseur', 'Superviseur'),
        ('validation', 'Agent de Validation'),
        ('admin', 'Administrateur'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='agent')
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

class SecteurActivite(models.Model):
    code = models.CharField(max_length=10, unique=True)
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} - {self.nom}"

class Region(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.nom

class Employeur(models.Model):
    STATUT_CHOICES = (
        ('prospecte', 'Prospecté'),
        ('dossier_soumis', 'Dossier Soumis'),
        ('en_cours', 'En Cours de Validation'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
    )
    
    numero_immatriculation = models.CharField(max_length=20, unique=True, blank=True)
    raison_sociale = models.CharField(max_length=200)
    nif = models.CharField(max_length=50, unique=True)
    rccm = models.CharField(max_length=50, unique=True)
    secteur_activite = models.ForeignKey(SecteurActivite, on_delete=models.PROTECT)
    region = models.ForeignKey(Region, on_delete=models.PROTECT)
    adresse = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    contact_nom = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_telephone = models.CharField(max_length=20)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='prospecte')
    motif_rejet = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    agent = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name='employeurs_crees')
    validated_by = models.ForeignKey(CustomUser, on_delete=models.PROTECT, null=True, blank=True, related_name='employeurs_valides')

    def save(self, *args, **kwargs):
        if not self.numero_immatriculation and self.statut == 'valide':
            self.numero_immatriculation = f"EMP{timezone.now().strftime('%Y%m')}{self.id:06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero_immatriculation} - {self.raison_sociale}"

class PieceJustificative(models.Model):
    employeur = models.ForeignKey(Employeur, on_delete=models.CASCADE, related_name='pieces_justificatives')
    nom = models.CharField(max_length=100)
    fichier = models.FileField(upload_to='pieces_justificatives/%Y/%m/')
    date_upload = models.DateTimeField(auto_now_add=True)

class Assure(models.Model):
    TYPE_ASSURE_CHOICES = (
        ('salarie', 'Salarié'),
        ('independant', 'Indépendant'),
        ('volontaire', 'Volontaire'),
    )
    
    numero_assure = models.CharField(max_length=20, unique=True, blank=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    lieu_naissance = models.CharField(max_length=100)
    numero_cni = models.CharField(max_length=50, unique=True)
    adresse = models.TextField()
    telephone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    type_assure = models.CharField(max_length=20, choices=TYPE_ASSURE_CHOICES)
    employeur = models.ForeignKey(Employeur, on_delete=models.CASCADE, null=True, blank=True, related_name='salaries')
    date_affiliation = models.DateTimeField(auto_now_add=True)
    est_actif = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.numero_assure:
            self.numero_assure = f"ASS{timezone.now().strftime('%Y%m')}{self.id:06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero_assure} - {self.prenom} {self.nom}"

class Declaration(models.Model):
    STATUT_CHOICES = (
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
    )
    
    employeur = models.ForeignKey(Employeur, on_delete=models.CASCADE, related_name='declarations')
    periode = models.DateField()  # Premier jour du mois de déclaration
    date_soumission = models.DateTimeField(null=True, blank=True)
    montant_total_cotisations = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    created_by = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['employeur', 'periode']

class LigneDeclaration(models.Model):
    declaration = models.ForeignKey(Declaration, on_delete=models.CASCADE, related_name='lignes')
    assure = models.ForeignKey(Assure, on_delete=models.PROTECT)
    salaire_declare = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    cotisation_salariale = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    cotisation_patronale = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

class Paiement(models.Model):
    MODE_PAIEMENT_CHOICES = (
        ('virement', 'Virement Bancaire'),
        ('cheque', 'Chèque'),
        ('mobile', 'Paiement Mobile'),
        ('guichet', 'Guichet'),
    )
    
    STATUT_PAIEMENT_CHOICES = (
        ('initie', 'Initié'),
        ('confirme', 'Confirmé'),
        ('rejete', 'Rejeté'),
    )
    
    reference = models.CharField(max_length=50, unique=True)
    declaration = models.ForeignKey(Declaration, on_delete=models.PROTECT, related_name='paiements')
    montant = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES)
    date_paiement = models.DateField()
    date_reception = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_PAIEMENT_CHOICES, default='initie')
    preuve_paiement = models.FileField(upload_to='preuves_paiement/%Y/%m/', null=True, blank=True)
    enregistre_par = models.ForeignKey(CustomUser, on_delete=models.PROTECT)

