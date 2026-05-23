from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QGroupBox, QComboBox, QMessageBox
)
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt, QThread, Signal
import requests


# ============================================================
# THREAD WORKER
# ============================================================

class Worker(QThread):
    finished = Signal(dict)

    def __init__(self, fn, *args):
        super().__init__()
        self.fn = fn
        self.args = args

    def run(self):
        result = self.fn(*self.args)
        self.finished.emit(result)


# ============================================================
# FICHE DOSSIER WINDOW
# ============================================================

class FicheDossierWindow(QWidget):

    def __init__(self, backend):
        super().__init__()
        self.backend = backend  # ton backend Python (API interne)
        self.setWindowTitle("Fiche Dossier Entreprise")
        self.setMinimumWidth(900)

        self.build_ui()

    # --------------------------------------------------------
    # UI COMPLETE
    # --------------------------------------------------------

    def build_ui(self):
        layout = QVBoxLayout(self)

        # -------------------------
        # Pavé Identité
        # -------------------------
        gb_identite = QGroupBox("Identité légale")
        grid_id = QGridLayout()

        self.le_siren = QLineEdit()
        self.le_nic = QLineEdit()
        self.le_siret = QLineEdit()
        self.le_tva_intracom = QLineEdit()

        self.btn_auto_fill = QPushButton("Remplir automatiquement")
        self.btn_auto_fill.clicked.connect(self.on_auto_fill_clicked)

        # Spinner
        self.spinner = QLabel()
        self.spinner_movie = QMovie("assets/spinner.gif")
        self.spinner.setMovie(self.spinner_movie)
        self.spinner.hide()

        grid_id.addWidget(QLabel("SIREN"), 0, 0)
        grid_id.addWidget(self.le_siren, 0, 1)

        grid_id.addWidget(QLabel("NIC"), 0, 2)
        grid_id.addWidget(self.le_nic, 0, 3)

        grid_id.addWidget(QLabel("SIRET"), 1, 0)
        grid_id.addWidget(self.le_siret, 1, 1, 1, 3)

        grid_id.addWidget(QLabel("TVA Intracom"), 2, 0)
        grid_id.addWidget(self.le_tva_intracom, 2, 1, 1, 3)

        grid_id.addWidget(self.btn_auto_fill, 3, 0, 1, 2)
        grid_id.addWidget(self.spinner, 3, 2)

        gb_identite.setLayout(grid_id)
        layout.addWidget(gb_identite)

        # -------------------------
        # Pavé Coordonnées
        # -------------------------
        gb_coord = QGroupBox("Coordonnées")
        grid_coord = QGridLayout()

        # Colonne gauche
        self.le_voie = QLineEdit()
        self.le_hameau = QLineEdit()
        self.le_complement = QLineEdit()
        self.le_code_postal = QLineEdit()
        self.le_ville = QLineEdit()
        self.cb_region = QComboBox()
        self.cb_region.addItems(["Guadeloupe", "Martinique", "Guyane", "Réunion"])
        self.cb_pays = QComboBox()
        self.cb_pays.addItems(["France", "Belgique", "Suisse"])

        # Colonne droite
        self.le_tel_fixe = QLineEdit()
        self.le_tel_portable = QLineEdit()
        self.le_email = QLineEdit()
        self.le_site_web = QLineEdit()
        self.le_responsable = QLineEdit()
        self.le_tel_responsable = QLineEdit()
        self.le_email_responsable = QLineEdit()

        # Colonne gauche
        grid_coord.addWidget(QLabel("Voie"), 0, 0)
        grid_coord.addWidget(self.le_voie, 0, 1)

        grid_coord.addWidget(QLabel("Hameau"), 1, 0)
        grid_coord.addWidget(self.le_hameau, 1, 1)

        grid_coord.addWidget(QLabel("Complément"), 2, 0)
        grid_coord.addWidget(self.le_complement, 2, 1)

        grid_coord.addWidget(QLabel("Code postal"), 3, 0)
        grid_coord.addWidget(self.le_code_postal, 3, 1)

        grid_coord.addWidget(QLabel("Ville"), 4, 0)
        grid_coord.addWidget(self.le_ville, 4, 1)

        grid_coord.addWidget(QLabel("Région"), 5, 0)
        grid_coord.addWidget(self.cb_region, 5, 1)

        grid_coord.addWidget(QLabel("Pays"), 6, 0)
        grid_coord.addWidget(self.cb_pays, 6, 1)

        # Colonne droite
        grid_coord.addWidget(QLabel("Téléphone fixe"), 0, 2)
        grid_coord.addWidget(self.le_tel_fixe, 0, 3)

        grid_coord.addWidget(QLabel("Téléphone portable"), 1, 2)
        grid_coord.addWidget(self.le_tel_portable, 1, 3)

        grid_coord.addWidget(QLabel("Email"), 2, 2)
        grid_coord.addWidget(self.le_email, 2, 3)

        grid_coord.addWidget(QLabel("Site web"), 3, 2)
        grid_coord.addWidget(self.le_site_web, 3, 3)

        grid_coord.addWidget(QLabel("Responsable"), 4, 2)
        grid_coord.addWidget(self.le_responsable, 4, 3)

        grid_coord.addWidget(QLabel("Tél. responsable"), 5, 2)
        grid_coord.addWidget(self.le_tel_responsable, 5, 3)

        grid_coord.addWidget(QLabel("Email responsable"), 6, 2)
        grid_coord.addWidget(self.le_email_responsable, 6, 3)

        gb_coord.setLayout(grid_coord)
        layout.addWidget(gb_coord)

        # -------------------------
        # Pavé Juridique
        # -------------------------
        gb_juridique = QGroupBox("Juridique")
        grid_j = QGridLayout()

        self.cb_forme_juridique = QComboBox()
        self.cb_forme_juridique.addItems(["SARL", "SAS", "SA", "EI"])

        self.le_siren_j = QLineEdit()
        self.le_nic_j = QLineEdit()
        self.le_frp = QLineEdit()
        self.le_cdi = QLineEdit()
        self.le_service = QLineEdit()
        self.le_siret_j = QLineEdit()
        self.le_naf = QLineEdit()
        self.le_naf_def = QLineEdit()
        self.le_naf_def.setReadOnly(True)
        self.le_rcs = QLineEdit()
        self.le_capital = QLineEdit()
        self.le_nb_parts = QLineEdit()

        grid_j.addWidget(QLabel("Forme juridique"), 0, 0)
        grid_j.addWidget(self.cb_forme_juridique, 0, 1)

        grid_j.addWidget(QLabel("SIREN"), 1, 0)
        grid_j.addWidget(self.le_siren_j, 1, 1)

        grid_j.addWidget(QLabel("NIC"), 1, 2)
        grid_j.addWidget(self.le_nic_j, 1, 3)

        grid_j.addWidget(QLabel("FRP"), 2, 0)
        grid_j.addWidget(self.le_frp, 2, 1)

        grid_j.addWidget(QLabel("CDI"), 2, 2)
        grid_j.addWidget(self.le_cdi, 2, 3)

        grid_j.addWidget(QLabel("SERVICE"), 3, 0)
        grid_j.addWidget(self.le_service, 3, 1)

        grid_j.addWidget(QLabel("SIRET"), 4, 0)
        grid_j.addWidget(self.le_siret_j, 4, 1, 1, 3)

        grid_j.addWidget(QLabel("Code NAF"), 5, 0)
        grid_j.addWidget(self.le_naf, 5, 1)

        grid_j.addWidget(QLabel("Définition NAF"), 5, 2)
        grid_j.addWidget(self.le_naf_def, 5, 3)

        grid_j.addWidget(QLabel("N° R.C"), 6, 0)
        grid_j.addWidget(self.le_rcs, 6, 1)

        grid_j.addWidget(QLabel("Capital social"), 7, 0)
        grid_j.addWidget(self.le_capital, 7, 1)

        grid_j.addWidget(QLabel("Nombre de parts"), 7, 2)
        grid_j.addWidget(self.le_nb_parts, 7, 3)

        gb_juridique.setLayout(grid_j)
        layout.addWidget(gb_juridique)

        # -------------------------
        # Pavé Fiscalité
        # -------------------------
        gb_fisc = QGroupBox("Fiscalité")
        grid_f = QGridLayout()

        self.cb_type_dossier = QComboBox()
        self.cb_type_dossier.addItems(["BIC", "BNC", "BA"])
        self.le_type_def = QLineEdit()
        self.le_type_def.setReadOnly(True)

        self.cb_regime_fiscal = QComboBox()
        self.cb_regime_fiscal.addItems(["RS", "RN", "RL"])
        self.le_regime_def = QLineEdit()
        self.le_regime_def.setReadOnly(True)

        self.cb_imposition = QComboBox()
        self.cb_imposition.addItems(["IS", "IR"])
        self.le_imposition_def = QLineEdit()
        self.le_imposition_def.setReadOnly(True)

        self.cb_regime_tva = QComboBox()
        self.cb_regime_tva.addItems(["Réel simplifié", "Réel normal", "Franchise"])
        self.le_tva_def = QLineEdit()
        self.le_tva_def.setReadOnly(True)

        self.le_tva_intracom_f = QLineEdit()

        grid_f.addWidget(QLabel("Type de dossier"), 0, 0)
        grid_f.addWidget(self.cb_type_dossier, 0, 1)
        grid_f.addWidget(self.le_type_def, 0, 2, 1, 2)

        grid_f.addWidget(QLabel("Régime fiscal"), 1, 0)
        grid_f.addWidget(self.cb_regime_fiscal, 1, 1)
        grid_f.addWidget(self.le_regime_def, 1, 2, 1, 2)

        grid_f.addWidget(QLabel("Imposition"), 2, 0)
        grid_f.addWidget(self.cb_imposition, 2, 1)
        grid_f.addWidget(self.le_imposition_def, 2, 2, 1, 2)

        grid_f.addWidget(QLabel("Régime TVA"), 3, 0)
        grid_f.addWidget(self.cb_regime_tva, 3, 1)
        grid_f.addWidget(self.le_tva_def, 3, 2, 1, 2)

        grid_f.addWidget(QLabel("TVA Intracom"), 4, 0)
        grid_f.addWidget(self.le_tva_intracom_f, 4, 1, 1, 3)

        gb_fisc.setLayout(grid_f)
        layout.addWidget(gb_fisc)

        # -------------------------
        # Bouton Enregistrer
        # -------------------------
        self.btn_save = QPushButton("Enregistrer les modifications")
        layout.addWidget(self.btn_save, alignment=Qt.AlignCenter)

        # -------------------------
        # Label d'état
        # -------------------------
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: grey; font-size: 11px;")
        layout.addWidget(self.lbl_status)

    # --------------------------------------------------------
    # AUTO-FILL
    # --------------------------------------------------------

    def on_auto_fill_clicked(self):
        siret = self.le_siret.text().strip()

        self.lbl_status.setText("")
        self.lbl_status.setStyleSheet("")

        if len(siret) != 14 or not siret.isdigit():
            self.lbl_status.setText("Le SIRET doit contenir 14 chiffres.")
            self.lbl_status.setStyleSheet("color: red; font-size: 11px;")
            return

        self.btn_auto_fill.setEnabled(False)
        self.btn_auto_fill.setText("⟳ Chargement…")
        self.spinner.show()
        self.spinner_movie.start()

        worker = Worker(self.fetch_siret_data_threaded, siret)
        worker.finished.connect(self.on_auto_fill_finished)
        worker.start()

    def fetch_siret_data_threaded(self, siret):
        try:
            data = self.backend.get_siret_data(siret)
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def on_auto_fill_finished(self, result):
        self.spinner_movie.stop()
        self.spinner.hide()

        self.btn_auto_fill.setEnabled(True)
        self.btn_auto_fill.setText("Remplir automatiquement")

        if result["success"]:
            self.fill_fields(result["data"])
            self.lbl_status.setText("Champs remplis automatiquement.")
            self.lbl_status.setStyleSheet("color: green; font-size: 11px;")
        else:
            self.lbl_status.setText("Aucune réponse de l’API INSEE.")
            self.lbl_status.setStyleSheet("color: red; font-size: 11px;")

    # --------------------------------------------------------
    # REMPLISSAGE AUTOMATIQUE
    # --------------------------------------------------------

    def fill_fields(self, data):

        def fill(widget, value):
            widget.setText(value)
            widget.setStyleSheet("color: #0066CC;")

        fill(self.le_voie, data.get("voie", ""))
        fill(self.le_ville, data.get("ville", ""))
        fill(self.le_code_postal, data.get("cp", ""))
        fill(self.le_naf, data.get("naf", ""))
        fill(self.le_siren_j, data.get("siren", ""))
        fill(self.le_siret_j, data.get("siret", ""))

        # etc. (tu complètes selon ton JSON)
