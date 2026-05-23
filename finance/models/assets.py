# -*- coding: utf-8 -*-
"""
Modèles pour la gestion des immobilisations (Assets)

- Asset : Immobilisation
- AssetDepreciation : Amortissement d'immobilisation
"""

from datetime import date
from decimal import Decimal
from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer,
    Numeric, String, Text, CheckConstraint, UniqueConstraint, func, Index
)
from sqlalchemy.orm import relationship

from backend.connection_manager import Base


class Asset(Base):
    """
    Immobilisation
    
    Représente une immobilisation corporelle ou incorporelle :
    - Matériel informatique
    - Véhicule
    - Brevet
    - Fonds de commerce
    - etc.
    
    Attributs :
        - code : Code unique de l'immobilisation
        - name : Nom/désignation
        - acquisition_date : Date d'acquisition
        - acquisition_value : Valeur d'acquisition HT
        - depreciation_method : Linéaire, dégressif, exceptionnel
        - depreciation_duration : Durée en années
        - accounting_account_id : Compte d'immobilisation (classe 2)
        - accumulated_depreciation : Total des amortissements cumulés
        - net_value : Valeur nette comptable
    """
    __tablename__ = "finance_assets"
    __table_args__ = (
        UniqueConstraint("dossier_id", "code", name="uq_finance_asset_code"),
        CheckConstraint("acquisition_value > 0", name="chk_finance_asset_value_positive"),
        CheckConstraint("depreciation_duration > 0", name="chk_finance_asset_duration_positive"),
        Index("idx_asset_dossier", "dossier_id"),
        Index("idx_asset_code", "code"),
        Index("idx_asset_category", "category"),
    )

    DEPRECIATION_METHODS = {
        "linear": "Linéaire",
        "degressive": "Dégressif",
        "exceptional": "Exceptionnel",
    }

    CATEGORIES = {
        "corporeal": "Immobilisations corporelles",
        "incorporeal": "Immobilisations incorporelles",
        "financial": "Immobilisations financières",
    }

    STATUS_CHOICES = {
        "active": "En service",
        "sold": "Cédé/Vendu",
        "scrapped": "Mis au rebut",
        "fully_depreciated": "Totalement amorti",
    }

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    fiscal_year_id = Column(Integer, ForeignKey("finance_fiscal_years.id"), nullable=False, index=True)
    
    # Identification
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Catégorie
    category = Column(String(20), nullable=False, default="corporeal")
    
    # Acquisition
    acquisition_date = Column(Date, nullable=False)
    acquisition_value = Column(Numeric(14, 2), nullable=False)
    supplier_name = Column(String(200), nullable=True)
    supplier_invoice_number = Column(String(50), nullable=True)
    
    # Amortissement
    depreciation_method = Column(String(20), nullable=False, default="linear")
    depreciation_duration = Column(Integer, nullable=False)  # En années
    depreciation_start_date = Column(Date, nullable=True)  # Peut différer de acquisition_date
    residual_value = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    
    # Comptabilité
    accounting_account_id = Column(Integer, ForeignKey("finance_accounts.id"), nullable=False, index=True)
    accumulated_depreciation_account_id = Column(Integer, ForeignKey("finance_accounts.id"), nullable=True)
    expense_account_id = Column(Integer, ForeignKey("finance_accounts.id"), nullable=True)  # Compte de charge d'amortissement
    
    # Statut
    status = Column(String(30), nullable=False, default="active")
    sale_date = Column(Date, nullable=True)
    sale_price = Column(Numeric(14, 2), nullable=True)
    sale_reason = Column(String(200), nullable=True)
    
    # Totaux calculés
    accumulated_depreciation = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    net_value = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    
    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    
    # Relations
    accounting_account = relationship("AccountingAccount", foreign_keys=[accounting_account_id])
    depreciations = relationship("AssetDepreciation", back_populates="asset", cascade="all, delete-orphan", order_by="AssetDepreciation.year")
    
    def __repr__(self):
        return f"<Asset(id={self.id}, code='{self.code}', name='{self.name}')>"
    
    @property
    def is_fully_depreciated(self) -> bool:
        """Vérifie si l'immobilisation est totalement amortie"""
        return self.net_value <= Decimal("0.00") or self.status == "fully_depreciated"
    
    @property
    def depreciation_rate(self) -> Decimal:
        """Calcule le taux d'amortissement annuel"""
        if self.depreciation_duration <= 0:
            return Decimal("0.00")
        
        if self.depreciation_method == "linear":
            return Decimal("100") / Decimal(self.depreciation_duration)
        elif self.depreciation_method == "degressive":
            # Coefficient dégressif selon durée (1.25, 1.75, 2.25)
            if self.depreciation_duration >= 6:
                coeff = Decimal("2.25")
            elif self.depreciation_duration >= 5:
                coeff = Decimal("1.75")
            else:
                coeff = Decimal("1.25")
            return (Decimal("100") / Decimal(self.depreciation_duration)) * coeff
        
        return Decimal("100") / Decimal(self.depreciation_duration)
    
    def calculate_annual_depreciation(self, year: int) -> Decimal:
        """
        Calcule le montant d'amortissement pour une année donnée
        
        Args:
            year: Année de calcul
            
        Returns:
            Montant d'amortissement annuel
        """
        if self.status != "active":
            return Decimal("0.00")
        
        base_value = self.acquisition_value - self.residual_value
        
        if self.depreciation_method == "linear":
            annual_amount = base_value / Decimal(self.depreciation_duration)
            
            # Prorata temporis pour première et dernière année
            if self.depreciation_start_date:
                start_year = self.depreciation_start_date.year
                end_year = start_year + self.depreciation_duration
                
                if year == start_year:
                    # Nombre de mois restants dans l'année
                    months_remaining = 13 - self.depreciation_start_date.month
                    return annual_amount * Decimal(months_remaining) / Decimal(12)
                elif year == end_year:
                    months_first_year = 13 - self.depreciation_start_date.month
                    months_last_year = 12 - (months_first_year % 12)
                    return annual_amount * Decimal(months_last_year) / Decimal(12)
                elif start_year < year < end_year:
                    return annual_amount
                else:
                    return Decimal("0.00")
            
            return annual_amount
        
        elif self.depreciation_method == "degressive":
            # Dégressif : taux appliqué à la valeur nette résiduelle
            rate = self.depreciation_rate / Decimal("100")
            remaining_base = self.acquisition_value - self.accumulated_depreciation
            
            # Passage en linéaire quand plus avantageux
            remaining_years = self.depreciation_duration - (year - self.depreciation_start_date.year)
            if remaining_years > 0:
                linear_rate = Decimal("100") / Decimal(remaining_years)
                if linear_rate > self.depreciation_rate:
                    return remaining_base / Decimal(remaining_years)
            
            return remaining_base * rate
        
        return Decimal("0.00")
    
    def update_net_value(self):
        """Met à jour la valeur nette comptable"""
        self.net_value = self.acquisition_value - self.accumulated_depreciation
        if self.net_value <= Decimal("0.00"):
            self.status = "fully_depreciated"


class AssetDepreciation(Base):
    """
    Amortissement d'immobilisation
    
    Enregistrement annuel de l'amortissement d'une immobilisation.
    Génère automatiquement les écritures comptables d'amortissement.
    
    Attributs :
        - year : Année d'amortissement
        - amount : Montant amorti
        - is_posted : Si l'écriture comptable a été générée
        - entry_id : Référence à l'écriture comptable générée
    """
    __tablename__ = "finance_asset_depreciations"
    __table_args__ = (
        UniqueConstraint("asset_id", "year", name="uq_finance_depreciation_asset_year"),
        CheckConstraint("amount >= 0", name="chk_finance_depreciation_amount_positive"),
        Index("idx_depreciation_asset", "asset_id"),
        Index("idx_depreciation_year", "year"),
    )

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("finance_assets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Année et période
    year = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Calculs
    depreciable_base = Column(Numeric(14, 2), nullable=False)
    depreciation_rate = Column(Numeric(5, 2), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    prorata_temporis = Column(Numeric(5, 4), nullable=False, default=Decimal("1.0000"))
    
    # Comptabilité
    is_posted = Column(Boolean, nullable=False, default=False)
    entry_id = Column(Integer, ForeignKey("finance_entries.id"), nullable=True, index=True)
    
    # Audit
    calculated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    posted_at = Column(DateTime(timezone=True), nullable=True)
    posted_by = Column(String(100), nullable=True)
    
    # Relations
    asset = relationship("Asset", back_populates="depreciations")
    entry = relationship("AccountingEntry", backref="asset_depreciations")
    
    def __repr__(self):
        return f"<AssetDepreciation(asset_id={self.asset_id}, year={self.year}, amount={self.amount})>"
    
    def calculate_amount(self, asset: Asset) -> Decimal:
        """
        Calcule le montant d'amortissement basé sur l'immobilisation
        
        Args:
            asset: L'immobilisation concernée
            
        Returns:
            Montant d'amortissement calculé
        """
        self.depreciable_base = asset.acquisition_value - asset.residual_value
        self.depreciation_rate = asset.depreciation_rate
        
        # Calcul avec prorata temporis
        months_in_year = min(12, 13 - self.start_date.month) if self.start_date.year == self.year else 12
        self.prorata_temporis = Decimal(months_in_year) / Decimal(12)
        
        self.amount = asset.calculate_annual_depreciation(self.year)
        return self.amount


# Import nécessaire pour UniqueConstraint
from sqlalchemy import UniqueConstraint
