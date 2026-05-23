from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView
import requests
import sys
import re
from modules.config import api_url

API_BASE = api_url("/dossiers")


class DossierListWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Liste des dossiers")
        self.setMinimumWidth(1100)
        self.setMinimumHeight(500)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- TITRE ---
        title = QLabel("Liste des dossiers")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # --- TABLEAU ---
        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "N° dossier",
            "Nom établissement",
            "Contact",
            "SIRET",
            "SIREN",
            "CP",
            "Ville",
            "N° fixe",
            "N° portable",
            "Email"
        ])
        self.table.setColumnHidden(0, True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)

        # Largeurs initiales des colonnes principales
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 220)
        self.table.setColumnWidth(3, 170)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(10, 220)

        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(self.table.SelectionMode.SingleSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSortingEnabled(True)
        self.table.setStyleSheet("""
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
        """)

        layout.addWidget(self.table)

        # --- BOUTONS ---
        btn_layout = QHBoxLayout()

        self.btn_open = QPushButton("Modifier")
        self.btn_delete = QPushButton("Supprimer")
        self.btn_create = QPushButton("Créer un dossier")

        # --- Couleurs douces ---
        self.btn_open.setStyleSheet("""
            QPushButton {
                background-color: #d9e7ff;
                border: 1px solid #a8c4ff;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c8dbff;
            }
        """)

        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #ffe0e0;
                border: 1px solid #ffb3b3;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ffcccc;
            }
        """)

        self.btn_create.setStyleSheet("""
            QPushButton {
                background-color: #e5ffe5;
                border: 1px solid #b3ffb3;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d0ffd0;
            }
        """)

        self.btn_refresh = QPushButton("Rafraîchir")
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                border: 1px solid #d1d5db;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        self._btn_refresh_default_style = self.btn_refresh.styleSheet()
        self._btn_refresh_active_style = """
            QPushButton {
                background-color: #fee2e2; /* rouge clair */
                border: 1px solid #f87171;
                color: #991b1b;
                padding: 6px;
                border-radius: 4px;
            }
        """

        btn_layout.addWidget(self.btn_open)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_create)
        btn_layout.addWidget(self.btn_refresh)


        layout.addLayout(btn_layout)

        # ⚠️ IMPORTANT : aucune connexion ici
        # Les boutons sont connectés dans DossiersModule (views.py)

        # --- Chargement initial ---
        self.load_dossiers()

    # ----------------------------------------------------------------------
    #  CHARGER LES DOSSIERS
    # ----------------------------------------------------------------------
    def load_dossiers(self):
        try:
            self.table.setSortingEnabled(False)
            self.table.clearContents()

            r = requests.get(API_BASE, timeout=10)
            r.raise_for_status()

            dossiers = r.json()
            self.table.setRowCount(len(dossiers))

            for row, d in enumerate(dossiers):
                num_dossier_recu = self._text(d.get("num_dossier"))

                self.table.setItem(row, 0, self._table_item(d.get("id")))
                self.table.setItem(row, 1, self._table_item(num_dossier_recu))
                self.table.setItem(row, 2, self._table_item(d.get("nom_entreprise")))
                self.table.setItem(row, 3, self._table_item(d.get("resp_nom")))
                self.table.setItem(row, 4, self._table_item(d.get("siret")))
                self.table.setItem(row, 5, self._table_item(d.get("siren")))
                self.table.setItem(row, 6, self._table_item(d.get("cp")))
                self.table.setItem(row, 7, self._table_item(d.get("ville")))
                self.table.setItem(row, 8, self._table_item(d.get("tel_fixe")))
                self.table.setItem(row, 9, self._table_item(d.get("tel_port")))
                self.table.setItem(row, 10, self._table_item(d.get("email")))

        except Exception as e:
            import traceback
            print("=== ERREUR load_dossiers ===")
            print(traceback.format_exc())
            QMessageBox.critical(self, "Erreur", repr(e))
        finally:
            self.table.setSortingEnabled(True)

    def _text(self, value):
        if value is None:
            return ""

        text = str(value)
        text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)
        text = text.replace("\b", "")
        text = re.sub(r"^\|b\s*", "", text)
        return text.strip()

    def _table_item(self, value):
        item = QTableWidgetItem(self._text(value))
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DossierListWindow()
    window.show()
    sys.exit(app.exec())
