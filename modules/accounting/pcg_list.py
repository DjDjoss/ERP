import requests
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from modules.accounting.pcg_edit import PCGEditWindow
from modules.config import api_url
from modules.realtime_events import RealtimeEventsThread


class PCGListWindow(QWidget):
    def __init__(self, dossier_id):
        super().__init__()

        self.dossier_id = int(dossier_id)
        self.accounts = []
        self._events_thread = None

        self.setWindowTitle("Plan Comptable General (PCG)")
        self.setMinimumSize(980, 620)

        layout = QVBoxLayout()

        title = QLabel(f"Plan Comptable - Dossier {dossier_id}")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        btn_add = QPushButton("Ajouter un compte")
        btn_add.clicked.connect(self.add_compte)
        layout.addWidget(btn_add)

        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.load_pcg()
        self._start_realtime_events()

    def load_pcg(self):
        try:
            response = requests.get(
                api_url(f"/accounting/dossiers/{self.dossier_id}/accounts"),
                timeout=15,
            )
            response.raise_for_status()
            self.accounts = response.json()
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger le PCG : {exc}")
            return

        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Compte", "Intitule", "Classe", "Type", "Modifier", "Supprimer"])
        self.table.setRowCount(len(self.accounts))

        for row_index, account in enumerate(self.accounts):
            self.table.setItem(row_index, 0, self._item(account.get("number")))
            self.table.setItem(row_index, 1, self._item(account.get("label")))
            self.table.setItem(row_index, 2, self._item(account.get("account_class")))
            self.table.setItem(row_index, 3, self._item(account.get("account_type")))

            btn_mod = QPushButton("Modifier")
            btn_mod.clicked.connect(lambda _, acc=account: self.edit_compte(acc))
            self.table.setCellWidget(row_index, 4, btn_mod)

            btn_sup = QPushButton("Supprimer")
            btn_sup.clicked.connect(lambda _, acc=account: self.delete_compte(acc))
            self.table.setCellWidget(row_index, 5, btn_sup)

        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(1, max(self.table.columnWidth(1), 360))

    def add_compte(self):
        dialog = PCGEditWindow(self.dossier_id)
        if dialog.exec():
            self.load_pcg()

    def edit_compte(self, account):
        dialog = PCGEditWindow(self.dossier_id, account)
        if dialog.exec():
            self.load_pcg()

    def delete_compte(self, account):
        number = account.get("number", "")
        confirm = QMessageBox.question(
            self,
            "Supprimer le compte",
            f"Supprimer le compte {number} ?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            response = requests.delete(
                api_url(f"/accounting/dossiers/{self.dossier_id}/accounts/{account['id']}"),
                timeout=10,
            )
            if not response.ok:
                raise RuntimeError(self._api_error_message(response))
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Suppression impossible : {exc}")
            return

        self.load_pcg()

    def _start_realtime_events(self):
        self._events_thread = RealtimeEventsThread(self)
        self._events_thread.event_received.connect(self._on_realtime_event)
        self._events_thread.start()

    def _on_realtime_event(self, event):
        if event.get("type") != "accounting_changed":
            return
        if int(event.get("dossier_id") or 0) != self.dossier_id:
            return
        self.load_pcg()

    def closeEvent(self, event):
        if self._events_thread:
            self._events_thread.stop()
            self._events_thread.wait(1000)
        super().closeEvent(event)

    def _item(self, value):
        item = QTableWidgetItem("" if value is None else str(value))
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    def _api_error_message(self, response):
        try:
            payload = response.json()
        except ValueError:
            return response.text

        if isinstance(payload, dict) and payload.get("detail"):
            return str(payload["detail"])
        return response.text
