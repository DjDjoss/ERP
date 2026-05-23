from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
import requests

from modules.accounting.dossier_manager import get_current_dossier
from modules.config import api_url


class Accounting2026Dashboard(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Comptabilite 2026 - ERP Rosan")
        self.setMinimumSize(950, 650)

        layout = QVBoxLayout(self)

        title = QLabel("Comptabilite ERP Rosan 2026")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Socle fonctionnel pour une comptabilite moderne, complete et conforme aux usages 2026."
        )
        subtitle.setStyleSheet("color: #374151; margin-bottom: 10px;")
        layout.addWidget(subtitle)

        action_layout = QHBoxLayout()
        self.btn_reload = QPushButton("Actualiser")
        self.btn_reload.clicked.connect(self.load_features)
        action_layout.addWidget(self.btn_reload)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Fonction", "Details"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #ffffff;
                alternate-background-color: #f6f8fb;
                border: 1px solid #d8dee9;
            }

            QTreeWidget::item {
                padding: 5px;
                color: #111827; /* texte lisible par défaut */
                background: transparent;
            }

            /* Survol souris */
            QTreeWidget::item:hover {
                background-color: #eaf2ff;
                color: #111827;
            }

            /* Sélection (clic) */
            QTreeWidget::item:selected {
                background-color: #1f6feb;
                color: #ffffff;
            }

            QHeaderView::section {
                background-color: #eef2f7;
                padding: 7px;
                border: 0;
                border-right: 1px solid #d8dee9;
                font-weight: 600;
            }
        """)
        layout.addWidget(self.tree)

        self.load_features()

    def load_features(self):
        try:
            response = requests.get(api_url("/accounting/features"), timeout=10)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger la comptabilite 2026 : {exc}")
            return

        self.tree.clear()
        dossier = get_current_dossier()

        if dossier:
            try:
                status_response = requests.get(
                    api_url(f"/accounting/dossiers/{dossier['id']}/status-2026"),
                    timeout=10,
                )
                status_response.raise_for_status()
                status = status_response.json()
                self._add_status_block(dossier, status)
            except Exception as exc:
                status_root = QTreeWidgetItem(["Etat dossier actif", f"Indisponible: {exc}"])
                self.tree.addTopLevelItem(status_root)
        else:
            status_root = QTreeWidgetItem(["Etat dossier actif", "Aucun dossier selectionne"])
            self.tree.addTopLevelItem(status_root)

        inventory = payload.get("inventory", {})
        inventory_root = QTreeWidgetItem(["Referentiel fonctionnel local", inventory.get("source_summary", "")])
        inventory_root.setExpanded(True)
        self.tree.addTopLevelItem(inventory_root)

        flags = [
            ("Referentiels detectes", "Oui" if inventory.get("installed") else "Non"),
            ("Perimetre comptable", "Oui" if inventory.get("accounting_data") else "Non"),
            ("Perimetre facturation", "Oui" if inventory.get("invoicing_data") else "Non"),
        ]
        for label, value in flags:
            inventory_root.addChild(QTreeWidgetItem([label, value]))

        accounting_files = inventory.get("accounting_reference_files", [])
        accounting_root = QTreeWidgetItem(["Referentiels comptables visibles", f"{len(accounting_files)} fichier(s)"])
        inventory_root.addChild(accounting_root)
        for name in accounting_files:
            accounting_root.addChild(QTreeWidgetItem([name, "Reference fonctionnelle locale"]))

        invoicing_files = inventory.get("invoicing_reference_files", [])
        invoicing_root = QTreeWidgetItem(["Referentiels facturation visibles", f"{len(invoicing_files)} fichier(s)"])
        inventory_root.addChild(invoicing_root)
        for name in invoicing_files:
            invoicing_root.addChild(QTreeWidgetItem([name, "Reference fonctionnelle locale"]))

        for block in payload.get("catalog", []):
            root = QTreeWidgetItem([block.get("title", ""), block.get("source", "")])
            root.setExpanded(True)
            self.tree.addTopLevelItem(root)

            for item in block.get("items", []):
                child = QTreeWidgetItem([item, "A integrer dans ERP Rosan"])
                child.setTextAlignment(0, Qt.AlignLeft | Qt.AlignVCenter)
                root.addChild(child)

        self.tree.resizeColumnToContents(0)

    def _add_status_block(self, dossier, status):
        nom = dossier.get("nom_entreprise") or dossier.get("nom") or f"Dossier {dossier.get('id')}"
        root = QTreeWidgetItem(["Etat dossier actif", nom])
        root.setExpanded(True)
        self.tree.addTopLevelItem(root)

        setup = status.get("setup", {})
        root.addChild(QTreeWidgetItem(["Socle dossier", "Pret" if setup.get("ready") else "A completer"]))
        root.addChild(QTreeWidgetItem(["Comptes PCG", str(setup.get("accounts", 0))]))
        root.addChild(QTreeWidgetItem(["Journaux", str(setup.get("journals", 0))]))
        root.addChild(QTreeWidgetItem(["Ecritures", str(setup.get("entries", 0))]))

        einvoice = QTreeWidgetItem(["Facturation electronique", f"{status.get('invoices', 0)} facture(s)"])
        einvoice.addChild(QTreeWidgetItem(["A transmettre/corriger", str(status.get("invoices_pending_platform", 0))]))
        root.addChild(einvoice)

        bank = QTreeWidgetItem(["Banque / rapprochement", f"{status.get('bank_transactions', 0)} operation(s)"])
        bank.addChild(QTreeWidgetItem(["Non rapprochees", str(status.get("bank_unmatched", 0))]))
        root.addChild(bank)

        vat = status.get("vat", {})
        vat_root = QTreeWidgetItem(["TVA", f"Nette due: {vat.get('net_vat_due', '0.00')}"])
        vat_root.addChild(QTreeWidgetItem(["Collectee", str(vat.get("collected_vat", "0.00"))]))
        vat_root.addChild(QTreeWidgetItem(["Deductible", str(vat.get("deductible_vat", "0.00"))]))
        root.addChild(vat_root)

        root.addChild(QTreeWidgetItem(["Piste d'audit", f"{status.get('audit_events', 0)} evenement(s)"]))

        controls = status.get("controls", [])
        controls_root = QTreeWidgetItem(["Controle des anomalies", f"{len(controls)} alerte(s)"])
        for issue in controls:
            controls_root.addChild(
                QTreeWidgetItem(
                    [
                        f"{issue.get('severity', '').upper()} - {issue.get('code', '')}",
                        f"{issue.get('message', '')} ({issue.get('count', 0)})",
                    ]
                )
            )
        root.addChild(controls_root)
