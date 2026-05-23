from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
import requests

from modules.accounting.dossier_manager import get_current_dossier
from modules.config import api_url


class AccountingReportWindow(QWidget):
    endpoint = ""
    title = ""
    headers = []
    keys = []

    def __init__(self):
        super().__init__()
        self.dossier = get_current_dossier()
        self.setWindowTitle(self.title)
        self.setMinimumSize(1000, 650)

        layout = QVBoxLayout(self)
        title = QLabel(self.title)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(self.table.SelectionMode.SingleSelection)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f6f8fb;
                gridline-color: #d8dee9;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
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
        layout.addWidget(self.table)
        self.load_data()

    def load_data(self):
        if self.dossier is None:
            QMessageBox.warning(self, "Aucun dossier", "Sélectionnez d'abord un dossier.")
            return

        try:
            response = requests.get(api_url(f"/accounting/dossiers/{self.dossier['id']}/{self.endpoint}"), timeout=10)
            response.raise_for_status()
            rows = response.json()
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger le rapport : {exc}")
            return

        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            for col_index, key in enumerate(self.keys):
                item = QTableWidgetItem(self.format_value(row.get(key, "")))
                item.setTextAlignment(self.alignment_for_key(key))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_index, col_index, item)

        self.table.resizeColumnsToContents()

    def format_value(self, value):
        if value is None:
            return ""
        return str(value)

    def alignment_for_key(self, key):
        if key in {"debit", "credit", "balance"}:
            return Qt.AlignRight | Qt.AlignVCenter
        return Qt.AlignLeft | Qt.AlignVCenter


class TrialBalanceWindow(AccountingReportWindow):
    endpoint = "trial-balance"
    title = "Balance comptable"
    headers = ["Compte", "Intitulé", "Débit", "Crédit", "Solde"]
    keys = ["account_number", "account_label", "debit", "credit", "balance"]


class GeneralLedgerWindow(AccountingReportWindow):
    endpoint = "ledger"
    title = "Grand livre"
    headers = ["Date", "Journal", "Pièce", "Compte", "Intitulé", "Libellé", "Débit", "Crédit", "Solde"]
    keys = [
        "entry_date",
        "journal_code",
        "piece_number",
        "account_number",
        "account_label",
        "label",
        "debit",
        "credit",
        "balance",
    ]


class VatSummaryWindow(AccountingReportWindow):
    endpoint = "vat-summary"
    title = "Synthese TVA"
    headers = ["TVA collectee", "TVA deductible", "TVA nette due"]
    keys = ["collected_vat", "deductible_vat", "net_vat_due"]

    def load_data(self):
        if self.dossier is None:
            QMessageBox.warning(self, "Aucun dossier", "Selectionnez d'abord un dossier.")
            return

        try:
            response = requests.get(api_url(f"/accounting/dossiers/{self.dossier['id']}/{self.endpoint}"), timeout=10)
            response.raise_for_status()
            row = response.json()
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger la TVA : {exc}")
            return

        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setRowCount(1)
        for col_index, key in enumerate(self.keys):
            item = QTableWidgetItem(self.format_value(row.get(key, "")))
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(0, col_index, item)
        self.table.resizeColumnsToContents()


class AccountingControlsWindow(AccountingReportWindow):
    endpoint = "controls"
    title = "Controle des anomalies"
    headers = ["Severite", "Code", "Message", "Nombre"]
    keys = ["severity", "code", "message", "count"]


class AuditLogWindow(AccountingReportWindow):
    endpoint = "audit-log"
    title = "Piste d'audit"
    headers = ["Date", "Action", "Entite", "ID", "Details"]
    keys = ["created_at", "action", "entity_type", "entity_id", "details"]


class ElectronicInvoicesWindow(AccountingReportWindow):
    endpoint = "invoices"
    title = "Facturation electronique"
    headers = ["Numero", "Partenaire", "SIRET", "Sens", "Date", "HT", "TVA", "TTC", "Format", "Statut plateforme", "Cycle"]
    keys = [
        "invoice_number",
        "partner_name",
        "partner_siret",
        "direction",
        "issue_date",
        "tax_excluded_amount",
        "vat_amount",
        "tax_included_amount",
        "format",
        "platform_status",
        "lifecycle_status",
    ]

    def __init__(self):
        super().__init__()
        btn_add = QPushButton("Ajouter une facture electronique")
        btn_add.clicked.connect(self.add_invoice)
        self.layout().insertWidget(1, btn_add)

    def add_invoice(self):
        dialog = ElectronicInvoiceDialog(self.dossier["id"], self)
        if dialog.exec():
            self.load_data()


class BankTransactionsWindow(AccountingReportWindow):
    endpoint = "bank-transactions"
    title = "Banque et rapprochement"
    headers = ["Date", "Libelle", "Montant", "Compte bancaire", "Statut", "Ecriture liee"]
    keys = ["transaction_date", "label", "amount", "bank_account", "reconciliation_status", "matched_entry_id"]

    def __init__(self):
        super().__init__()
        btn_add = QPushButton("Ajouter une operation bancaire")
        btn_add.clicked.connect(self.add_transaction)
        self.layout().insertWidget(1, btn_add)

    def add_transaction(self):
        dialog = BankTransactionDialog(self.dossier["id"], self)
        if dialog.exec():
            self.load_data()


class ElectronicInvoiceDialog(QDialog):
    def __init__(self, dossier_id, parent=None):
        super().__init__(parent)
        self.dossier_id = dossier_id
        self.setWindowTitle("Ajouter une facture electronique")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.invoice_number = QLineEdit()
        self.partner_name = QLineEdit()
        self.partner_siret = QLineEdit()
        self.direction = QComboBox()
        self.direction.addItems(["outgoing", "incoming"])
        self.issue_date = QLineEdit()
        self.issue_date.setPlaceholderText("AAAA-MM-JJ")
        self.due_date = QLineEdit()
        self.due_date.setPlaceholderText("AAAA-MM-JJ")
        self.ht = QLineEdit("0.00")
        self.vat = QLineEdit("0.00")
        self.ttc = QLineEdit("0.00")
        self.format = QComboBox()
        self.format.addItems(["factur-x", "ubl", "cii"])
        self.platform_status = QComboBox()
        self.platform_status.addItems(["draft", "pending", "sent", "accepted", "rejected", "error"])
        self.lifecycle_status = QComboBox()
        self.lifecycle_status.addItems(["draft", "issued", "received", "paid", "cancelled"])

        form.addRow("Numero", self.invoice_number)
        form.addRow("Partenaire", self.partner_name)
        form.addRow("SIRET partenaire", self.partner_siret)
        form.addRow("Sens", self.direction)
        form.addRow("Date emission", self.issue_date)
        form.addRow("Date echeance", self.due_date)
        form.addRow("Montant HT", self.ht)
        form.addRow("TVA", self.vat)
        form.addRow("Montant TTC", self.ttc)
        form.addRow("Format", self.format)
        form.addRow("Statut plateforme", self.platform_status)
        form.addRow("Cycle de vie", self.lifecycle_status)
        layout.addLayout(form)

        btn_save = QPushButton("Enregistrer")
        btn_save.clicked.connect(self.save)
        layout.addWidget(btn_save)

    def save(self):
        payload = {
            "invoice_number": self.invoice_number.text().strip(),
            "partner_name": self.partner_name.text().strip(),
            "partner_siret": self.partner_siret.text().strip() or None,
            "direction": self.direction.currentText(),
            "issue_date": self.issue_date.text().strip(),
            "due_date": self.due_date.text().strip() or None,
            "tax_excluded_amount": self.ht.text().strip() or "0.00",
            "vat_amount": self.vat.text().strip() or "0.00",
            "tax_included_amount": self.ttc.text().strip() or "0.00",
            "format": self.format.currentText(),
            "platform_status": self.platform_status.currentText(),
            "lifecycle_status": self.lifecycle_status.currentText(),
        }
        self._post(api_url(f"/accounting/dossiers/{self.dossier_id}/invoices"), payload)

    def _post(self, url, payload):
        try:
            response = requests.post(url, json=payload, timeout=10)
            if not response.ok:
                raise RuntimeError(response.json().get("detail", response.text))
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Enregistrement impossible : {exc}")
            return
        self.accept()


class BankTransactionDialog(QDialog):
    def __init__(self, dossier_id, parent=None):
        super().__init__(parent)
        self.dossier_id = dossier_id
        self.setWindowTitle("Ajouter une operation bancaire")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.transaction_date = QLineEdit()
        self.transaction_date.setPlaceholderText("AAAA-MM-JJ")
        self.label = QLineEdit()
        self.amount = QLineEdit("0.00")
        self.bank_account = QLineEdit()
        self.status = QComboBox()
        self.status.addItems(["unmatched", "matched", "ignored"])

        form.addRow("Date", self.transaction_date)
        form.addRow("Libelle", self.label)
        form.addRow("Montant", self.amount)
        form.addRow("Compte bancaire", self.bank_account)
        form.addRow("Statut", self.status)
        layout.addLayout(form)

        btn_save = QPushButton("Enregistrer")
        btn_save.clicked.connect(self.save)
        layout.addWidget(btn_save)

    def save(self):
        payload = {
            "transaction_date": self.transaction_date.text().strip(),
            "label": self.label.text().strip(),
            "amount": self.amount.text().strip() or "0.00",
            "bank_account": self.bank_account.text().strip() or None,
            "reconciliation_status": self.status.currentText(),
        }
        try:
            response = requests.post(
                api_url(f"/accounting/dossiers/{self.dossier_id}/bank-transactions"),
                json=payload,
                timeout=10,
            )
            if not response.ok:
                raise RuntimeError(response.json().get("detail", response.text))
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Enregistrement impossible : {exc}")
            return
        self.accept()


class FecExportWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.dossier = get_current_dossier()
        self.setWindowTitle("Export FEC")
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout(self)
        title = QLabel("Export FEC")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        self.btn_reload = QPushButton("Generer / actualiser")
        self.btn_reload.clicked.connect(self.load_data)
        layout.addWidget(self.btn_reload)

        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        self.load_data()

    def load_data(self):
        if self.dossier is None:
            QMessageBox.warning(self, "Aucun dossier", "Selectionnez d'abord un dossier.")
            return

        try:
            response = requests.get(api_url(f"/accounting/dossiers/{self.dossier['id']}/fec"), timeout=15)
            response.raise_for_status()
            lines = [line.split("\t") for line in response.text.splitlines() if line]
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Impossible de generer le FEC : {exc}")
            return

        if not lines:
            self.table.setRowCount(0)
            return

        headers, rows = lines[0], lines[1:]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_index, col_index, item)
        self.table.resizeColumnsToContents()
