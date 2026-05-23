from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel
)
from core.database import get_connection


class FournisseurListWindow(QWidget):
    def __init__(self, dossier_id):
        super().__init__()

        self.dossier_id = dossier_id

        self.setWindowTitle("Liste des fournisseurs")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout()

        title = QLabel("Liste des fournisseurs du dossier")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Tableau
        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.load_fournisseurs()

    def load_fournisseurs(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, nom, secteur, siren, adresse
            from fournisseurs
            WHERE dossier_id = ?
        """, (self.dossier_id,))

        rows = cursor.fetchall()
        conn.close()

        # Configuration du tableau
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Nom", "Secteur", "SIREN", "Adresse"])
        self.table.setRowCount(len(rows))

        for row_index, row_data in enumerate(rows):
            for col_index, value in enumerate(row_data):
                self.table.setItem(row_index, col_index, QTableWidgetItem(str(value)))

        self.table.resizeColumnsToContents()
