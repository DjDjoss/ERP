# -*- coding: utf-8 -*-
"""
Saisie d'une écriture comptable - Interface PySide6
Utilise PostgreSQL comme base de données
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QMessageBox, QLabel, QCompleter, QDialog
)
from PySide6.QtCore import Qt
from core.db_postgresql import get_dossier_session
from finance.models.core import AccountingAccount as Account, AccountingJournal as Journal
from finance.models.entries import AccountingEntry, AccountingEntryLine
from datetime import date


class EcritureSaisieWindow(QDialog):
    def __init__(self, dossier_id, db_name, parent=None):
        super().__init__(parent)
        
        self.dossier_id = dossier_id
        self.db_name = db_name
        
        self.setWindowTitle("Saisie d'une écriture")
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout()
        
        # --- FORMULAIRE EN-TÊTE ---
        form = QFormLayout()
        
        self.journal = QComboBox()
        self.load_journaux()
        
        self.date_edit = QLineEdit(date.today().isoformat())
        self.numero_piece = QLineEdit()
        self.libelle = QLineEdit()
        
        form.addRow("Journal :", self.journal)
        form.addRow("Date :", self.date_edit)
        form.addRow("N° pièce :", self.numero_piece)
        form.addRow("Libellé :", self.libelle)
        
        layout.addLayout(form)
        
        # --- CHARGEMENT DES COMPTES POUR SUGGESTION ---
        self.comptes_codes = self.load_comptes_codes()
        self.completer = QCompleter(self.comptes_codes)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        
        # --- TABLE DES LIGNES ---
        self.table = QTableWidget(4, 4)
        self.table.setHorizontalHeaderLabels(["Compte", "Libellé", "Débit", "Crédit"])
        layout.addWidget(self.table)
        
        # Prépare les 4 premières lignes avec auto-complétion sur la colonne Compte
        for r in range(4):
            self.init_row_widgets(r)
        
        # --- BOUTONS ---
        btn_add = QPushButton("Ajouter une ligne")
        btn_add.clicked.connect(self.add_row)
        layout.addWidget(btn_add)
        
        btn_save = QPushButton("Enregistrer l'écriture")
        btn_save.clicked.connect(self.save_ecriture)
        layout.addWidget(btn_save)
        
        self.setLayout(layout)
    
    def load_journaux(self):
        """Charge les journaux depuis PostgreSQL"""
        session = get_dossier_session(self.db_name)
        try:
            journals = session.query(Journal).filter(
                Journal.dossier_id == self.dossier_id
            ).order_by(Journal.code.asc()).all()
            
            for journal in journals:
                self.journal.addItem(journal.code, journal.id)
        finally:
            session.close()
    
    def load_comptes_codes(self):
        """Charge les comptes depuis PostgreSQL"""
        session = get_dossier_session(self.db_name)
        try:
            accounts = session.query(Account).filter(
                Account.dossier_id == self.dossier_id,
                Account.actif == True
            ).order_by(Account.number.asc()).all()
            
            return [acc.number for acc in accounts]
        finally:
            session.close()
    
    def init_row_widgets(self, row):
        # Colonne Compte avec auto-complétion
        compte_edit = QLineEdit()
        compte_edit.setCompleter(self.completer)
        self.table.setCellWidget(row, 0, compte_edit)
        
        # Libellé, Débit, Crédit en QTableWidgetItem
        self.table.setItem(row, 1, QTableWidgetItem(""))
        self.table.setItem(row, 2, QTableWidgetItem(""))
        self.table.setItem(row, 3, QTableWidgetItem(""))
    
    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.init_row_widgets(row)
    
    def save_ecriture(self):
        """Enregistre l'écriture dans PostgreSQL"""
        journal_code = self.journal.currentText()
        if not journal_code:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un journal.")
            return
            
        date_ecriture = self.date_edit.text().strip()
        numero_piece = self.numero_piece.text().strip()
        libelle = self.libelle.text().strip()
        
        # Vérification date
        try:
            date.fromisoformat(date_ecriture)
        except:
            QMessageBox.warning(self, "Erreur", "La date doit être au format AAAA-MM-JJ.")
            return
        
        total_debit = 0.0
        total_credit = 0.0
        lignes = []
        
        for r in range(self.table.rowCount()):
            compte_widget = self.table.cellWidget(r, 0)
            lib_item = self.table.item(r, 1)
            debit_item = self.table.item(r, 2)
            credit_item = self.table.item(r, 3)
            
            if compte_widget is None:
                continue
            
            compte = compte_widget.text().strip()
            if compte == "":
                continue
            
            lib_ligne = lib_item.text().strip() if lib_item else ""
            d = float(debit_item.text()) if debit_item and debit_item.text() != "" else 0.0
            c = float(credit_item.text()) if credit_item and credit_item.text() != "" else 0.0
            
            total_debit += d
            total_credit += c
            
            lignes.append((compte, lib_ligne, d, c))
        
        if len(lignes) == 0:
            QMessageBox.warning(self, "Erreur", "Aucune ligne saisie.")
            return
        
        if abs(total_debit - total_credit) > 0.001:
            QMessageBox.warning(
                self, 
                "Erreur", 
                f"L'écriture n'est pas équilibrée.\nDébit: {total_debit:.2f} €\nCrédit: {total_credit:.2f} €\nÉcart: {abs(total_debit - total_credit):.2f} €"
            )
            return
        
        session = get_dossier_session(self.db_name)
        try:
            # Récupérer l'ID du journal
            journal = session.query(Journal).filter(
                Journal.code == journal_code,
                Journal.dossier_id == self.dossier_id
            ).first()
            
            if not journal:
                QMessageBox.warning(self, "Erreur", f"Le journal {journal_code} n'existe pas.")
                return
            
            # Créer l'écriture
            entry = FinanceEntry(
                dossier_id=self.dossier_id,
                journal_id=journal.id,
                date=date_ecriture,
                reference=numero_piece or None,
                description=libelle,
                amount=total_debit,
                posted=False
            )
            
            session.add(entry)
            session.flush()  # Pour obtenir l'ID
            
            # Créer les lignes
            for compte_num, lib_ligne, debit, credit in lignes:
                account = session.query(Account).filter(
                    Account.number == compte_num,
                    Account.dossier_id == self.dossier_id
                ).first()
                
                if not account:
                    QMessageBox.warning(
                        self, 
                        "Erreur", 
                        f"Le compte {compte_num} n'existe pas dans le plan comptable."
                    )
                    session.rollback()
                    return
                
                line = FinanceEntryLine(
                    entry_id=entry.id,
                    account_id=account.id,
                    description=lib_ligne or libelle,
                    debit=debit,
                    credit=credit
                )
                session.add(line)
            
            session.commit()
            QMessageBox.information(self, "Succès", "Écriture enregistrée avec succès.")
            self.accept()
            
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement: {str(e)}")
        finally:
            session.close()
