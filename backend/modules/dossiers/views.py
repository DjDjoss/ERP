from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from .dossier_create_dialog import DossierCreateDialog


class DossiersModule(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        btn_create = QPushButton("Créer un dossier")
        btn_create.clicked.connect(self.open_create_dialog)

        layout.addWidget(btn_create)

    def open_create_dialog(self):
        dialog = DossierCreateDialog(self)
        dialog.exec()
