import requests
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from modules.config import api_url


class PCGEditWindow(QDialog):
    def __init__(self, dossier_id, account=None):
        super().__init__()

        self.dossier_id = dossier_id
        self.account = account or {}
        self.account_id = self.account.get("id")

        self.setWindowTitle("Modifier un compte" if self.account_id else "Ajouter un compte")
        self.setMinimumSize(420, 260)

        layout = QVBoxLayout()
        form = QFormLayout()

        self.numero = QLineEdit()
        self.intitule = QLineEdit()
        self.type = QLineEdit("general")
        self.actif = QCheckBox("Compte actif")
        self.actif.setChecked(True)

        form.addRow("Numero de compte :", self.numero)
        form.addRow("Intitule :", self.intitule)
        form.addRow("Type :", self.type)
        form.addRow("", self.actif)

        layout.addLayout(form)

        btn = QPushButton("Enregistrer")
        btn.clicked.connect(self.save)
        layout.addWidget(btn)

        self.setLayout(layout)
        self.load_data()

    def load_data(self):
        if not self.account:
            return

        self.numero.setText(str(self.account.get("number") or ""))
        self.intitule.setText(str(self.account.get("label") or ""))
        self.type.setText(str(self.account.get("account_type") or "general"))
        self.actif.setChecked(bool(self.account.get("is_active", True)))

    def save(self):
        numero = self.numero.text().strip()
        intitule = self.intitule.text().strip()
        type_cpt = self.type.text().strip() or "general"

        if not numero or not intitule:
            QMessageBox.warning(self, "Erreur", "Les champs numero et intitule sont obligatoires.")
            return

        payload = {
            "number": numero,
            "label": intitule,
            "account_class": numero[0] if numero else "",
            "account_type": type_cpt,
            "is_active": self.actif.isChecked(),
        }

        try:
            if self.account_id:
                response = requests.put(
                    api_url(f"/accounting/dossiers/{self.dossier_id}/accounts/{self.account_id}"),
                    json=payload,
                    timeout=10,
                )
            else:
                response = requests.post(
                    api_url(f"/accounting/dossiers/{self.dossier_id}/accounts"),
                    json=payload,
                    timeout=10,
                )

            if not response.ok:
                raise RuntimeError(self._api_error_message(response))
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Compte non enregistre : {exc}")
            return

        QMessageBox.information(self, "Succes", "Compte enregistre avec succes.")
        self.accept()

    def _api_error_message(self, response):
        try:
            payload = response.json()
        except ValueError:
            return response.text

        if isinstance(payload, dict) and payload.get("detail"):
            return str(payload["detail"])
        return response.text
