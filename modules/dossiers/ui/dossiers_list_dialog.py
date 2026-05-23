from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QPushButton, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, QPoint
import requests
import re
from modules.config import api_url


class DossiersListDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Liste des dossiers")
        self.resize(1100, 600)

        self.selected_id = None

        self.build_ui()
        self.load_dossiers()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "N° dossier",
            "Nom",
            "Contact",
            "SIRET",
            "SIREN-NIC",
            "CP",
            "Ville",
            "Région",
            "N° fixe",
            "N° portable",
            "Email",
        ])

        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setSelectionMode(self.table.SingleSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)

        self.table.setStyleSheet(
            """
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f6f8fb;
                gridline-color: #d8dee9;
                selection-background-color: #1f6feb;
                selection-color: #ffffff;
            }
            QTableWidget::item {
                padding: 6px;
                border: 0;
            }
            QTableWidget::item:hover {
                background-color: #eaf2ff;
                color: #111827;
            }
            QTableWidget::item:selected {
                background-color: #1f6feb;
                color: #ffffff;
                font-weight: 600;
                outline: 0;
            }
            QTableWidget::item:focus {
                outline: 0;
            }
            QHeaderView::section {
                background-color: #eef2f7;
                color: #111827;
                padding: 7px;
                border: 0;
                border-right: 1px solid #d8dee9;
                border-bottom: 1px solid #cbd5e1;
                font-weight: 600;
            }
            """
        )

        layout.addWidget(self.table)

        # Boutons
        btn_layout = QHBoxLayout()
        self.btn_open = QPushButton("Sélectionner")
        self.btn_edit = QPushButton("Modifier")
        self.btn_delete = QPushButton("Supprimer")

        self.btn_open.clicked.connect(self.open_selected_dossier)
        self.btn_edit.clicked.connect(self.edit_selected_dossier)
        self.btn_delete.clicked.connect(self.delete_selected_dossier)

        btn_layout.addWidget(self.btn_open)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)

        layout.addLayout(btn_layout)


    # ---------------------------------------------------------
    # CRÉER UN DOSSIER
    # ---------------------------------------------------------
    def open_create_dialog(self):
        from .dossier_create_dialog import DossierCreateDialog
        dlg = DossierCreateDialog(self)

        # Si l’utilisateur clique sur "Enregistrer et Quitter"
        if dlg.exec() == QDialog.Accepted:
            self.load_dossiers()   # recharge la liste



    # ---------------------------------------------------------
    # CHARGEMENT DES DOSSIERS
    # ---------------------------------------------------------
    def load_dossiers(self):
        try:
            resp = requests.get(api_url("/dossiers"), timeout=5)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les dossiers : {e}")
            return

        self.table.setRowCount(len(data))

        for row, d in enumerate(data):
            siren_nic = f"{d.get('siren','')} - {d.get('nic','')}"
            values = [
                d.get("num_dossier", ""),
                d.get("nom_entreprise", ""),
                d.get("resp_nom", ""),
                d.get("siret", ""),
                siren_nic,
                d.get("cp", ""),
                d.get("ville", ""),
                d.get("region", ""),
                d.get("tel_fixe", ""),
                d.get("tel_port", ""),
                d.get("email", ""),
            ]

            for col, val in enumerate(values):
                item = QTableWidgetItem(self.clean_cell_text(val))
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setData(Qt.UserRole, d.get("id"))
                self.table.setItem(row, col, item)

    def clean_cell_text(self, value):
        if value is None:
            return ""

        text = str(value)
        text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)
        text = text.replace("\b", "")
        text = re.sub(r"^\|b\s*", "", text)
        return text.strip()

    # ---------------------------------------------------------
    # RÉCUPÉRATION ID SÉLECTIONNÉ
    # ---------------------------------------------------------
    def get_selected_dossier_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole)

    # ---------------------------------------------------------
    # SÉLECTIONNER
    # ---------------------------------------------------------
    def open_selected_dossier(self):
        dossier_id = self.get_selected_dossier_id()
        if dossier_id is None:
            QMessageBox.warning(self, "Info", "Veuillez sélectionner un dossier.")
            return

        self.selected_id = dossier_id
        self.accept()

    # ---------------------------------------------------------
    # MODIFIER
    # ---------------------------------------------------------
    def edit_selected_dossier(self):
        dossier_id = self.get_selected_dossier_id()
        if dossier_id is None:
            QMessageBox.warning(self, "Info", "Veuillez sélectionner un dossier.")
            return

        # Récupération API
        try:
            url = api_url(f"/dossiers/{dossier_id}")
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger le dossier : {e}")
            return

        # Ouverture fenêtre modification
        from .dossier_create_dialog import DossierCreateDialog
        dlg = DossierCreateDialog()
        dlg.load_from_api(data)
        dlg.exec()

        self.load_dossiers()

    # ---------------------------------------------------------
    # CONFIRMATION SUPPRESSION (4 étapes)
    # ---------------------------------------------------------
    def confirm_delete(self) -> bool:
        messages = [
            "Voulez-vous vraiment supprimer ce dossier ?",
            "Cette action est irréversible. Confirmez-vous la suppression ?",
            "Toutes les données associées seront définitivement perdues.\nÊtes-vous absolument certain ?",
            "Dernière confirmation : supprimer le dossier ?",
        ]

        for msg in messages:
            reply = QMessageBox.question(
                self, "Confirmation", msg,
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return False

        return True

    # ---------------------------------------------------------
    # SUPPRIMER
    # ---------------------------------------------------------
    def delete_selected_dossier(self):
        dossier_id = self.get_selected_dossier_id()
        if dossier_id is None:
            QMessageBox.warning(self, "Info", "Veuillez sélectionner un dossier.")
            return

        if not self.confirm_delete():
            return

        try:
            url = api_url(f"/dossiers/{dossier_id}")
            resp = requests.delete(url, timeout=5)
            resp.raise_for_status()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression : {e}")
            return

        QMessageBox.information(self, "Succès", "Dossier supprimé.")
        self.load_dossiers()

    # ---------------------------------------------------------
    # MENU CLIC DROIT
    # ---------------------------------------------------------
    def open_context_menu(self, pos: QPoint):
        menu = QMenu(self)

        action_open = menu.addAction("Sélectionner")
        action_edit = menu.addAction("Modifier")
        action_delete = menu.addAction("Supprimer")

        action = menu.exec(self.table.mapToGlobal(pos))

        if action == action_open:
            self.open_selected_dossier()
        elif action == action_edit:
            self.edit_selected_dossier()
        elif action == action_delete:
            self.delete_selected_dossier()
