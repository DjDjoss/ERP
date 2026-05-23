from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox
)
from core.database import get_connection


class JournalCreateWindow(QWidget):
    def __init__(self, dossier_id):
        super().__init__()

        self.dossier_id = dossier_id

        self.setWindowTitle("Créer un journal")
        self.setMinimumSize(400, 200)

        layout = QVBoxLayout()
        form = QFormLayout()

        self.code = QLineEdit()
        self.libelle = QLineEdit()

        form.addRow("Code du journal :", self.code)
        form.addRow("Libellé :", self.libelle)

        layout.addLayout(form)

        btn = QPushButton("Enregistrer")
        btn.clicked.connect(self.save_journal)
        layout.addWidget(btn)

        self.setLayout(layout)

    def save_journal(self):
        code = self.code.text().strip().upper()
        libelle = self.libelle.text().strip()

        if code == "" or libelle == "":
            QMessageBox.warning(self, "Erreur", "Tous les champs sont obligatoires.")
            return

        conn = get_connection()
        cursor = conn.cursor()

        # Vérifier unicité
        cursor.execute("""
            SELECT id from modules.accounting.journaux
            WHERE dossier_id = ? AND code = ?
        """, (self.dossier_id, code))

        if cursor.fetchone():
            QMessageBox.warning(self, "Erreur", "Ce code de journal existe déjà.")
            conn.close()
            return

        cursor.execute("""
            INSERT INTO journaux (dossier_id, code, libelle, actif)
            VALUES (?, ?, ?, 1)
        """, (self.dossier_id, code, libelle))

        conn.commit()
        conn.close()

        QMessageBox.information(self, "Journal créé", f"Le journal {code} a été ajouté.")
        self.close()
