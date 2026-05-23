from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QFormLayout,
    QMessageBox, QComboBox, QHBoxLayout
)
from core.database import get_connection


class ClientCreateWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Créer un client")
        self.setMinimumSize(450, 350)

        layout = QVBoxLayout()
        form = QFormLayout()

        # --- Champs du client ---
        self.nom = QLineEdit()
        self.nom.setPlaceholderText("Nom de l'entreprise (obligatoire)")

        self.secteur = QComboBox()
        self.secteur.addItems([
            "Commerce",
            "Services",
            "BTP",
            "Restauration",
            "Transport",
            "Santé",
            "Informatique",
            "Association",
            "Autre"
        ])

        self.siren = QLineEdit()
        self.siren.setPlaceholderText("9 chiffres")

        self.adresse = QLineEdit()
        self.adresse.setPlaceholderText("Adresse complète")

        form.addRow("Nom du client * :", self.nom)
        form.addRow("Secteur d'activité :", self.secteur)
        form.addRow("SIREN :", self.siren)
        form.addRow("Adresse :", self.adresse)

        layout.addLayout(form)

        # --- Boutons ---
        btn_layout = QHBoxLayout()

        btn_save = QPushButton("Enregistrer")
        btn_save.clicked.connect(self.save_client)

        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.close)

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    # --- Validation SIREN ---
    def validate_siren(self, siren):
        return siren.isdigit() and len(siren) == 9

    # --- Enregistrement ---
    def save_client(self):
        nom = self.nom.text().strip()
        secteur = self.secteur.currentText()
        siren = self.siren.text().strip()
        adresse = self.adresse.text().strip()

        # Champs obligatoires
        if nom == "":
            QMessageBox.warning(self, "Erreur", "Le nom du client est obligatoire.")
            return

        # Validation SIREN
        if siren != "" and not self.validate_siren(siren):
            QMessageBox.warning(self, "Erreur", "Le SIREN doit contenir exactement 9 chiffres.")
            return

        # Enregistrement en base
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO clients (nom, secteur, siren, adresse)
            VALUES (?, ?, ?, ?)
        """, (nom, secteur, siren, adresse))

        conn.commit()
        conn.close()

        QMessageBox.information(
            self,
            "Client enregistré",
            f"Le client '{nom}' a été enregistré avec succès."
        )

        self.close()
