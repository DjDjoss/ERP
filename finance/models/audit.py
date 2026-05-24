# -*- coding: utf-8 -*-
"""
Modèle de log d'audit

- AuditLog : Trace toutes les actions importantes
  sur les données comptables (création, modification,
  suppression, validation, etc.)
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)

from core.db_postgresql import Base


class AuditLog(Base):
    """
    Log d'audit comptable
    
    Enregistre toutes les opérations critiques :
    - Création/modification/suppression d'écritures
    - Validation/annulation
    - Clôture d'exercice
    - Export FEC
    - Modifications de paramètres
    
    Conforme aux exigences de piste d'audit FEC.
    """
    __tablename__ = "finance_audit_logs"

    ACTION_TYPES = [
        "CREATE",
        "UPDATE",
        "DELETE",
        "VALIDATE",
        "CANCEL",
        "CLOSE",
        "REOPEN",
        "EXPORT",
        "IMPORT",
        "CONFIG_CHANGE",
    ]

    ENTITY_TYPES = [
        "FiscalYear",
        "AccountingJournal",
        "AccountingAccount",
        "AccountingEntry",
        "AccountingEntryLine",
        "BankAccount",
        "BankTransaction",
        "BankReconciliation",
        "TrialBalance",
        "GeneralLedger",
    ]

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    
    # Action
    action_type = Column(String(30), nullable=False)  # CREATE, UPDATE, DELETE, etc.
    entity_type = Column(String(50), nullable=False)  # Type d'entité concernée
    entity_id = Column(Integer, nullable=True)  # ID de l'entité
    entity_label = Column(String(200), nullable=True)  # Libellé descriptif
    
    # Détails
    old_values = Column(Text, nullable=True)  # JSON des anciennes valeurs
    new_values = Column(Text, nullable=True)  # JSON des nouvelles valeurs
    changes_summary = Column(String(500), nullable=True)  # Résumé lisible des changements
    
    # Contexte
    user_login = Column(String(100), nullable=True)  # Utilisateur ayant fait l'action
    user_ip = Column(String(45), nullable=True)  # Adresse IP
    user_agent = Column(String(500), nullable=True)  # Navigateur/client
    
    # Timestamp
    action_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Métadonnées additionnelles (renommé pour éviter conflit avec SQLAlchemy)
    audit_metadata = Column("metadata", Text, nullable=True)  # JSON pour données complémentaires

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action_type}', entity='{self.entity_type}')>"

    @classmethod
    def log(cls, db_session, action_type: str, entity_type: str, entity_id: int = None,
            entity_label: str = None, old_values: dict = None, new_values: dict = None,
            user_login: str = None, user_ip: str = None, audit_metadata: dict = None):
        """
        Crée un nouvel enregistrement de log d'audit.
        
        Args:
            db_session : Session SQLAlchemy
            action_type : Type d'action (CREATE, UPDATE, DELETE, etc.)
            entity_type : Type d'entité (AccountingEntry, etc.)
            entity_id : ID de l'entité concernée
            entity_label : Libellé descriptif
            old_values : Anciennes valeurs (dict)
            new_values : Nouvelles valeurs (dict)
            user_login : Identifiant utilisateur
            user_ip : Adresse IP
            audit_metadata : Métadonnées additionnelles
        """
        import json
        
        log_entry = cls(
            dossier_id=0,  # Sera mis à jour si disponible
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_label=entity_label,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            user_login=user_login,
            user_ip=user_ip,
            audit_metadata=json.dumps(audit_metadata) if audit_metadata else None,
        )
        
        db_session.add(log_entry)
        db_session.commit()
        
        return log_entry
