from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QMessageBox, QLabel, QCompleter
)
from PySide6.QtCore import Qt
from core.database import get_connection
import datetime


class EcritureSaisieWindow(QWidget):
    def __init__(self, dossier_id):
        super().__init__()

        self.dossier_id = dossier_id

        self.setWindowTitle("Saisie d'une écriture")
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout()

        # --- FORMULAIRE EN-TÊTE ---
        form = QFormLayout()

        self.journal = QComboBox()
        self.load_journaux()

        self.date = QLineEdit(datetime.date.today().isoformat())
        self.numero_piece = QLineEdit()
        self.libelle = QLineEdit()

        form.addRow("Journal :", self.journal)
        form.addRow("Date :", self.date)
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
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT code from journaux
            WHERE dossier_id = ?
            ORDER BY code ASC
        """, (self.dossier_id,))
        rows = cursor.fetchall()
        conn.close()

        for r in rows:
            self.journal.addItem(r[0])

    def load_comptes_codes(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT compte from comptes
            WHERE dossier_id = ? AND actif = 1
            ORDER BY compte ASC
        """, (self.dossier_id,))
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows]

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
        journal_code = self.journal.currentText()
        date_ecriture = self.date.text().strip()
        numero_piece = self.numero_piece.text().strip()
        libelle = self.libelle.text().strip()

        # Vérification date
        try:
            datetime.date.fromisoformat(date_ecriture)
        except:
            QMessageBox.warning(self, "Erreur", "La date doit être au format AAAA-MM-JJ.")
            return

        total_debit = 0
        total_credit = 0
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
            d = float(debit_item.text()) if debit_item and debit_item.text() != "" else 0
            c = float(credit_item.text()) if credit_item and credit_item.text() != "" else 0

            total_debit += d
            total_credit += c

            lignes.append((compte, lib_ligne, d, c))

        if len(lignes) == 0:
            QMessageBox.warning(self, "Erreur", "Aucune ligne saisie.")
            return

        if abs(total_debit - total_credit) > 0.0001:
            QMessageBox.warning(self, "Erreur", "L'écriture n'est pas équilibrée.")
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ecritures (dossier_id, journal_code, date_ecriture, numero_piece, libelle, montant_total)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (self.dossier_id, journal_code, date_ecriture, numero_piece, libelle, total_debit))

        ecriture_id = cursor.lastrowid

        for compte, lib_ligne, d, c in lignes:
            cursor.execute("""
                INSERT INTO ecritures_lignes (ecriture_id, dossier_id, journal_code, compte, libelle_ligne, debit, credit)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ecriture_id, self.dossier_id, journal_code, compte, lib_ligne, d, c))

        conn.commit()
        conn.close()

        QMessageBox.information(self, "Succès", "Écriture enregistrée.")
        self.close()
