from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox
)
from core.database import get_connection
from modules.accounting.dossier_manager import set_current_dossier


class DossierOpenWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ouvrir un dossier")
        self.setMinimumSize(500, 300)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tableau des dossiers
        self.table = QTableWidget()
        layout.addWidget(self.table)

        # Bouton d'ouverture
        btn = QPushButton("Ouvrir le dossier sélectionné")
        btn.clicked.connect(self.open_selected)
        layout.addWidget(btn)

        # Charger les dossiers
        self.load_dossiers()

    def load_dossiers(self):
        """Charge la liste des dossiers dans la table."""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, nom, annee FROM dossiers ORDER BY nom")
        rows = cursor.fetchall()
        conn.close()

        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nom", "Exercice"])
        self.table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(value)))

        self.table.resizeColumnsToContents()

    def open_selected(self):
        """Ouvre le dossier sélectionné et met à jour l'état global."""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Erreur", "Sélectionnez un dossier.")
            return

        dossier_id = int(self.table.item(selected, 0).text())
        nom = self.table.item(selected, 1).text()
        annee = self.table.item(selected, 2).text()

        dossier = {
            "id": dossier_id,
            "nom": nom,
            "annee": annee
        }

        # Mise à jour du dossier courant
        set_current_dossier(dossier)

        # Fermer la fenêtre modale
        self.accept()
