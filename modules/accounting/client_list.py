from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel
)
from core.database import get_connection


class ClientListWindow(QWidget):
    def __init__(self, dossier_id=None):
        super().__init__()

        self.dossier_id = dossier_id  # <-- Ajout demandé

        self.setWindowTitle("Liste des clients")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout()

        title = QLabel("Liste des clients enregistrés")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Tableau
        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.load_clients()

    def load_clients(self):
        conn = get_connection()
        cursor = conn.cursor()

        # --- Requête conditionnelle selon dossier_id ---
        if self.dossier_id:
            cursor.execute(
                "SELECT id, nom, secteur, siren, adresse FROM clients WHERE dossier_id = ?",
                (self.dossier_id,)
            )
        else:
            cursor.execute(
                "SELECT id, nom, secteur, siren, adresse FROM clients"
            )

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
