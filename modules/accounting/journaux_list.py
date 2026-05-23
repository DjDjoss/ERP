from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton, QMessageBox
)
from core.database import get_connection


class JournauxListWindow(QWidget):
    def __init__(self, dossier_id):
        super().__init__()

        self.dossier_id = dossier_id

        self.setWindowTitle("Journaux comptables")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout()

        title = QLabel("Journaux du dossier")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.setLayout(layout)

        self.load_journaux()

    def load_journaux(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT code, libelle, actif
            from journaux
            WHERE dossier_id = ?
            ORDER BY code ASC
        """, (self.dossier_id,))

        rows = cursor.fetchall()
        conn.close()

        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Code", "Libellé", "Actif", "Supprimer"])
        self.table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            code, libelle, actif = row
            self.table.setItem(r, 0, QTableWidgetItem(str(code)))
            self.table.setItem(r, 1, QTableWidgetItem(str(libelle)))
            self.table.setItem(r, 2, QTableWidgetItem("Oui" if actif else "Non"))

            btn = QPushButton("Supprimer")
            btn.clicked.connect(lambda _, c=code: self.delete_journal(c))
            self.table.setCellWidget(r, 3, btn)

        self.table.resizeColumnsToContents()

    def delete_journal(self, code):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) from modules.accounting.ecritures
            WHERE dossier_id = ? AND journal_code = ?
        """, (self.dossier_id, code))
        nb = cursor.fetchone()[0]

        if nb > 0:
            QMessageBox.warning(
                self,
                "Impossible",
                "Ce journal contient des écritures et ne peut pas être supprimé."
            )
            conn.close()
            return

        cursor.execute("""
            DELETE from modules.accounting.journaux
            WHERE dossier_id = ? AND code = ?
        """, (self.dossier_id, code))

        conn.commit()
        conn.close()

        QMessageBox.information(self, "Journal supprimé", f"Le journal {code} a été supprimé.")
        self.load_journaux()
