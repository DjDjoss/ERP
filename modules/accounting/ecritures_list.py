from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QComboBox
)
from core.database import get_connection


class EcrituresListWindow(QWidget):
    def __init__(self, dossier_id):
        super().__init__()

        self.dossier_id = dossier_id

        self.setWindowTitle("Liste des écritures")
        self.setMinimumSize(900, 500)

        layout = QVBoxLayout()

        # --- FILTRE JOURNAL ---
        self.journal = QComboBox()
        self.load_journaux()
        self.journal.currentIndexChanged.connect(self.load_ecritures)
        layout.addWidget(self.journal)

        # --- TABLE ---
        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.load_ecritures()

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

    def load_ecritures(self):
        journal_code = self.journal.currentText()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, date_ecriture, numero_piece, libelle, montant_total
            from modules.accounting.ecritures
            WHERE dossier_id = ? AND journal_code = ?
            ORDER BY date_ecriture ASC
        """, (self.dossier_id, journal_code))

        rows = cursor.fetchall()
        conn.close()

        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Date", "Pièce", "Libellé", "Montant"])
        self.table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(value)))

        self.table.resizeColumnsToContents()
