# -*- coding: utf-8 -*-
"""
Modèles du module Dossiers

Un dossier représente un client/entreprise dans l'ERP multi-tenancy.
Chaque dossier a sa propre base de données PostgreSQL isolée.
"""

from datetime import date
from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer,
    Numeric, String, Text, UniqueConstraint, CheckConstraint, func, Index
)
from sqlalchemy.orm import relationship

from core.db_postgresql import Base


class Dossier(Base):
    """
    Dossier client - Entité principale du multi-tenancy
    
    Chaque dossier représente une entreprise cliente avec :
    - Ses propres données comptables
    - Sa propre base de données PostgreSQL
    - Ses propres utilisateurs et permissions
    
    Attributs :
        - nom_entreprise : Nom légal de l'entreprise
        - siren : Numéro SIREN (9 chiffres)
        - siret : Numéro SIRET (14 chiffres)
        - code_naf : Code NAF/APE
        - tva_intracom : Numéro TVA intracommunautaire
        - statut : Actif, suspendu, fermé
    """
    __tablename__ = "dossiers"
    __table_args__ = (
        UniqueConstraint("siren", name="uq_dossiers_siren"),
        Index("idx_dossier_nom", "nom_entreprise"),
        Index("idx_dossier_statut", "statut"),
    )

    STATUT_CHOICES = {
        "actif": "Actif",
        "suspendu": "Suspendu",
        "ferme": "Fermé",
        "en_creation": "En création",
    }

    id = Column(Integer, primary_key=True, index=True)
    
    # Identification entreprise
    nom_entreprise = Column(String(200), nullable=False)
    nom_commercial = Column(String(200), nullable=True)
    siren = Column(String(9), nullable=True, index=True)
    siret = Column(String(14), nullable=True)
    code_naf = Column(String(5), nullable=True)
    tva_intracom = Column(String(20), nullable=True)
    
    # Adresse
    adresse_ligne1 = Column(String(200), nullable=True)
    adresse_ligne2 = Column(String(200), nullable=True)
    code_postal = Column(String(10), nullable=True)
    ville = Column(String(100), nullable=True)
    pays = Column(String(100), nullable=True, default="France")
    
    # Contact
    telephone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    site_web = Column(String(200), nullable=True)
    
    # Représentant légal
    dirigeant_nom = Column(String(100), nullable=True)
    dirigeant_fonction = Column(String(100), nullable=True)
    
    # Comptabilité
    expert_comptable_nom = Column(String(100), nullable=True)
    expert_comptable_cabinet = Column(String(200), nullable=True)
    expert_comptable_email = Column(String(100), nullable=True)
    
    # Configuration
    statut = Column(String(20), nullable=False, default="en_creation")
    date_creation = Column(Date, nullable=False, default=func.now())
    date_cloture_exercice = Column(Integer, nullable=True, default=31)  # Jour de clôture (ex: 31 pour décembre)
    devise_principale = Column(String(3), nullable=False, default="EUR")
    
    # Base de données
    db_name = Column(String(100), nullable=True, unique=True)  # Nom de la DB PostgreSQL
    db_host = Column(String(100), nullable=True)
    db_port = Column(Integer, nullable=True, default=5432)
    
    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    
    # Relations
    # Note: La relation avec Dossier est gérée via dossier_id uniquement
    # Pas de back_populates car Dossier et FiscalYear sont dans des modules/bases différents
    fiscal_years = relationship(
        "FiscalYear",
        primaryjoin="Dossier.id == foreign(FiscalYear.dossier_id)",
        cascade="all, delete-orphan",
        overlaps="journals,accounts"
    )
    journals = relationship(
        "AccountingJournal",
        primaryjoin="Dossier.id == foreign(AccountingJournal.dossier_id)",
        cascade="all, delete-orphan"
    )
    accounts = relationship(
        "AccountingAccount",
        primaryjoin="Dossier.id == foreign(AccountingAccount.dossier_id)",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Dossier(id={self.id}, nom='{self.nom_entreprise}', siren='{self.siren}')>"
    
    @property
    def is_active(self) -> bool:
        """Vérifie si le dossier est actif"""
        return self.statut == "actif"
    
    @property
    def full_address(self) -> str:
        """Retourne l'adresse complète formatée"""
        parts = []
        if self.adresse_ligne1:
            parts.append(self.adresse_ligne1)
        if self.adresse_ligne2:
            parts.append(self.adresse_ligne2)
        if self.code_postal and self.ville:
            parts.append(f"{self.code_postal} {self.ville}")
        if self.pays:
            parts.append(self.pays)
        return "\n".join(parts)
    
    @property
    def formatted_tva(self) -> str:
        """Formate le numéro TVA intracommunautaire"""
        if not self.tva_intracom:
            return ""
        # Format français : FR + 2 caractères + SIREN
        if len(self.tva_intracom) >= 11:
            return self.tva_intracom
        if self.siren:
            return f"FR{self.siren}"
        return self.tva_intracom


class DossierDocument(Base):
    """
    Document attaché à un dossier
    
    Permet de stocker des documents légaux, statuts, KBIS, etc.
    """
    __tablename__ = "dossiers_documents"
    __table_args__ = (
        Index("idx_document_dossier", "dossier_id"),
        Index("idx_document_type", "document_type"),
    )

    DOCUMENT_TYPES = {
        "kbis": "Extrait K-BIS",
        "statuts": "Statuts",
        "pv_ag": "PV Assemblée Générale",
        "bilan": "Bilan annuel",
        "contrat": "Contrat de mission",
        "autre": "Autre",
    }

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    document_type = Column(String(30), nullable=False)
    label = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Fichier
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(200), nullable=False)
    file_size = Column(Numeric(12, 0), nullable=True)  # En octets
    mime_type = Column(String(100), nullable=True)
    
    # Métadonnées
    document_date = Column(Date, nullable=True)
    is_confidential = Column(Boolean, nullable=False, default=False)
    
    # Audit
    uploaded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    uploaded_by = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<DossierDocument(id={self.id}, type='{self.document_type}', file='{self.file_name}')>"


class DossierContact(Base):
    """
    Contact associé à un dossier
    
    Personnes à contacter dans l'entreprise cliente
    """
    __tablename__ = "dossiers_contacts"
    __table_args__ = (
        Index("idx_contact_dossier", "dossier_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Identité
    civilite = Column(String(10), nullable=True)  # M., Mme, Dr., etc.
    prenom = Column(String(100), nullable=False)
    nom = Column(String(100), nullable=False)
    
    # Fonction
    fonction = Column(String(100), nullable=True)
    departement = Column(String(100), nullable=True)
    
    # Coordonnées
    telephone_bureau = Column(String(20), nullable=True)
    telephone_mobile = Column(String(20), nullable=True)
    email = Column(String(100), nullable=False)
    
    # Préférences
    est_contact_principal = Column(Boolean, nullable=False, default=False)
    peut_se_connecter = Column(Boolean, nullable=False, default=False)  # Accès au portail client
    
    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    
    def __repr__(self):
        return f"<DossierContact(id={self.id}, nom='{self.nom}', email='{self.email}')>"
    
    @property
    def full_name(self) -> str:
        """Retourne le nom complet"""
        parts = []
        if self.civilite:
            parts.append(self.civilite)
        parts.append(self.prenom)
        parts.append(self.nom)
        return " ".join(parts)
