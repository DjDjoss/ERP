from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt
import requests

# --- Import des vraies fenêtres ---
from modules.dossiers.dossier_create_dialog import DossierCreateDialog   # ✔ NOUVELLE FENÊTRE PRO
from modules.dossiers.ui.dossier_list_window import DossierListWindow

from modules.accounting.pcg_list import PCGListWindow
from modules.accounting.journaux_list import JournauxListWindow
from modules.accounting.journaux_create import JournalCreateWindow
from modules.accounting.ecritures_list import EcrituresListWindow
from modules.accounting.ecriture_saisie import EcritureSaisieWindow
from modules.accounting.client_list import ClientListWindow
from modules.accounting.client_create import ClientCreateWindow
from modules.accounting.fournisseur_list import FournisseurListWindow
from modules.accounting.fournisseur_create import FournisseurCreateWindow
from modules.accounting.accounting_2026_dashboard import Accounting2026Dashboard
from modules.accounting.accounting_reports import (
    AccountingControlsWindow,
    AuditLogWindow,
    BankTransactionsWindow,
    ElectronicInvoicesWindow,
    FecExportWindow,
    GeneralLedgerWindow,
    TrialBalanceWindow,
    VatSummaryWindow,
)
from modules.config import api_url

# Gestion du dossier courant
from modules.accounting.dossier_manager import (
    get_current_dossier,
    set_current_dossier,
    delete_dossier_with_alerts,
    update_window_title
)
from modules.realtime_events import RealtimeEventsThread


class AccountingModule(QWidget):
    def __init__(self):
        super().__init__()

        self._refresh_dossiers_in_progress = False


        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(12, 8, 12, 12)
        self.layout.setSpacing(6)
        self.setLayout(self.layout)
        self.child_windows = []
        self.current_dossier_label = QLabel("Aucun dossier sélectionné")
        self.current_dossier_label.setMinimumHeight(38)
        self.current_dossier_label.setMaximumHeight(46)
        self.current_dossier_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.current_dossier_label.setStyleSheet(
            """
            QLabel {
                background-color: #174ea6;
                color: white;
                border: 1px solid #123d82;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 17px;
                font-weight: 700;
            }
            """
        )

        # --- SECTION DOSSIERS ---
        self.btn_dashboard_2026 = QPushButton("Tableau de bord Comptabilité 2026")
        self.btn_create = QPushButton("Créer un dossier")
        self.btn_modify = QPushButton("Modifier un dossier")
        self.btn_delete = QPushButton("Supprimer un dossier")

        # Fusion : bouton "Sélectionner un dossier" + libellé du dossier sélectionné
        # placés en haut à droite sur la même ligne que le titre du module.
        self._dossier_select_row = QHBoxLayout()
        self._dossier_select_row.setContentsMargins(0, 0, 0, 0)
        self._dossier_select_row.setSpacing(8)

        self.btn_open = QPushButton("Sélectionner un dossier")
        self.btn_open.setMinimumHeight(34)

        self.current_dossier_label.setMinimumHeight(34)
        self.current_dossier_label.setMaximumHeight(34)
        self.current_dossier_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        # Agrandit en largeur quand la fenêtre grandit
        self.current_dossier_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Etat initial (aucun dossier sélectionné)
        self.current_dossier_label.setText("Aucun Dossier Actif")
        self.current_dossier_label.setStyleSheet(
            """
            QLabel {
                background-color: #174ea6;
                color: white;
                border: 1px solid #123d82;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 17px;
                font-weight: 700;
            }
            """
        )



        # Forcer le bloc “Sélectionner un dossier / dossier actif” à rester à droite
        # sur la même ligne que le titre du module : on le place comme “élément droit”
        # dans une vraie ligne d’en-tête (QHBoxLayout) et non comme simple ligne au-dessus.
        self._header_row = QHBoxLayout()
        self._header_row.setContentsMargins(0, 0, 0, 0)
        self._header_row.setSpacing(8)

        # “Espace” pour le titre du module (laissé vide ici car dans ton UI le titre
        # est probablement géré par le parent ; ce spacer garantit l'alignement à droite).
        self._header_row.addStretch(1)

        self._dossier_select_row.setContentsMargins(0, 0, 0, 0)
        self._dossier_select_row.setSpacing(8)
        self._dossier_select_row.addWidget(self.btn_open)
        self._dossier_select_row.addWidget(self.current_dossier_label, 1)

        self._header_row.addLayout(self._dossier_select_row)
        self.layout.addLayout(self._header_row)




        # Ligne boutons créer/modifier/supprimer
        dossier_actions_bandelette = QHBoxLayout()
        dossier_actions_bandelette.setSpacing(6)
        dossier_actions_bandelette.addWidget(self.btn_create)
        dossier_actions_bandelette.addWidget(self.btn_modify)
        dossier_actions_bandelette.addWidget(self.btn_delete)
        self.layout.addLayout(dossier_actions_bandelette)


        # Les 3 boutons + Rafraîchir doivent être sur la même ligne
        dossier_actions = QHBoxLayout()
        dossier_actions.setSpacing(6)
        dossier_actions.addWidget(self.btn_create)
        dossier_actions.addWidget(self.btn_modify)
        dossier_actions.addWidget(self.btn_delete)

        # Rafraîchir (liste dossiers compta) — même ligne + mêmes règles que gestion dossiers
        self.btn_refresh_dossiers = QPushButton("Rafraîchir")
        # Même taille que les autres boutons (padding/hauteur via style + minimum height)
        self.btn_refresh_dossiers.setMinimumHeight(34)
        self.btn_create.setMinimumHeight(34)
        self.btn_modify.setMinimumHeight(34)
        self.btn_delete.setMinimumHeight(34)

        self.btn_refresh_dossiers.clicked.connect(self.refresh_dossier_list_and_select)

        # Couleurs cohérentes avec modules/dossiers/ui/dossier_list_window.py
        self.btn_refresh_dossiers.setStyleSheet(
            """
            QPushButton {
                background-color: #f3f4f6;
                border: 1px solid #d1d5db;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
            QPushButton:disabled {
                background-color: #f3f4f6;
                border: 1px solid #d1d5db;
                color: #9ca3af;
            }
            """
        )

        # Même couleur “soft” que les autres boutons pour le backend (Créer/Modifier/Supprimer)
        # on conserve le style refresh gris, comme dans la gestion dossiers.


        self._btn_refresh_dossiers_default_style = self.btn_refresh_dossiers.styleSheet()
        self._btn_refresh_dossiers_active_style = """
            QPushButton {
                background-color: #fee2e2; /* rouge clair */
                border: 1px solid #f87171;
                color: #991b1b;
                padding: 6px;
                border-radius: 4px;
            }
        """

        dossier_actions.addWidget(self.btn_refresh_dossiers)

        # --- Couleurs cohérentes avec modules/dossiers/ui/dossier_list_window.py ---
        # Modifier/Créer/Supprimer (et leurs couleurs soft)
        self.btn_create.setStyleSheet("""
            QPushButton {
                background-color: #e5ffe5;
                border: 1px solid #b3ffb3;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #d0ffd0; }
        """)

        self.btn_modify.setStyleSheet("""
            QPushButton {
                background-color: #d9e7ff;
                border: 1px solid #a8c4ff;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #c8dbff; }
        """)

        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #ffe0e0;
                border: 1px solid #ffb3b3;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #ffcccc; }
        """)

        # Rafraîchir (conservé gris normal + style clignotant rouge clair)

        self.layout.addLayout(dossier_actions)


        # --- SECTION COMPTA ---

        # bouton tableau de bord doit apparaître comme avant
        self.layout.addWidget(self.btn_dashboard_2026)

        self.btn_pcg = QPushButton("Plan Comptable")


        self.btn_journaux = QPushButton("Journaux")
        self.btn_journal_create = QPushButton("Créer un Journal")
        self.btn_ecritures = QPushButton("Liste des Écritures")
        self.btn_ecriture_saisie = QPushButton("Saisie d'Écriture")
        self.btn_clients = QPushButton("Clients")
        self.btn_client_create = QPushButton("Créer un Client")
        self.btn_fournisseurs = QPushButton("Fournisseurs")
        self.btn_fournisseur_create = QPushButton("Créer un Fournisseur")
        self.btn_balance = QPushButton("Balance")
        self.btn_grand_livre = QPushButton("Grand Livre")
        self.btn_tva = QPushButton("TVA")
        self.btn_fec = QPushButton("FEC")
        self.btn_audit = QPushButton("Piste d'audit")
        self.btn_controls = QPushButton("Contrôles")
        self.btn_invoices = QPushButton("Facturation électronique")
        self.btn_bank = QPushButton("Banque / rapprochement")

        self.compta_buttons = [
            self.btn_pcg, self.btn_journaux, self.btn_journal_create,
            self.btn_ecritures, self.btn_ecriture_saisie,
            self.btn_clients, self.btn_client_create,
            self.btn_fournisseurs, self.btn_fournisseur_create,
            self.btn_balance, self.btn_grand_livre,
            self.btn_tva, self.btn_fec, self.btn_audit, self.btn_controls,
            self.btn_invoices, self.btn_bank
        ]

        for btn in self.compta_buttons:
            btn.setEnabled(False)
            self.layout.addWidget(btn)

        # --- Connexions ---
        self.btn_dashboard_2026.clicked.connect(self.open_dashboard_2026)
        self.btn_open.clicked.connect(self.open_dossier)
        self.btn_create.clicked.connect(self.create_dossier)
        self.btn_modify.clicked.connect(self.modify_dossier)
        self.btn_delete.clicked.connect(self.delete_dossier)

        self.btn_pcg.clicked.connect(self.open_pcg)
        self.btn_journaux.clicked.connect(lambda: self.open_window(JournauxListWindow))
        self.btn_journal_create.clicked.connect(lambda: self.open_window(JournalCreateWindow))
        self.btn_ecritures.clicked.connect(lambda: self.open_window(EcrituresListWindow))
        self.btn_ecriture_saisie.clicked.connect(lambda: self.open_window(EcritureSaisieWindow))
        self.btn_clients.clicked.connect(lambda: self.open_window(ClientListWindow))
        self.btn_client_create.clicked.connect(lambda: self.open_window(ClientCreateWindow))
        self.btn_fournisseurs.clicked.connect(lambda: self.open_window(FournisseurListWindow))
        self.btn_fournisseur_create.clicked.connect(lambda: self.open_window(FournisseurCreateWindow))

        self.btn_balance.clicked.connect(lambda: self.open_window(TrialBalanceWindow))
        self.btn_grand_livre.clicked.connect(lambda: self.open_window(GeneralLedgerWindow))
        self.btn_tva.clicked.connect(lambda: self.open_window(VatSummaryWindow))
        self.btn_fec.clicked.connect(lambda: self.open_window(FecExportWindow))
        self.btn_audit.clicked.connect(lambda: self.open_window(AuditLogWindow))
        self.btn_controls.clicked.connect(lambda: self.open_window(AccountingControlsWindow))
        self.btn_invoices.clicked.connect(lambda: self.open_window(ElectronicInvoicesWindow))
        self.btn_bank.clicked.connect(lambda: self.open_window(BankTransactionsWindow))

        # --- Clignotement du bouton “Rafraîchir” ---
        # 1) Clignote ~20s après un ajout/modif/suppression de dossier côté utilisateur
        # 2) Puis re-clignotement uniquement si de nouveaux dossiers apparaissent (poll toutes les 5 minutes)
        self._last_accounting_dossier_count = None
        self._blink_countdown = 0
        self._accounting_refresh_blink_timer = None
        self._accounting_manual_blink_timer = None

        # Initialiser le compteur de base (s'il est possible)
        self._last_accounting_dossier_count = 0

        from PySide6.QtCore import QTimer
        self._accounting_refresh_blink_timer = QTimer(self)
        self._accounting_refresh_blink_timer.setInterval(300000)  # 5 minutes
        self._accounting_refresh_blink_timer.timeout.connect(self._check_new_dossiers_and_blink)
        self._accounting_refresh_blink_timer.start()

        # Mise à jour initiale
        self.refresh_state()

        self._events_thread = RealtimeEventsThread(self)
        self._events_thread.event_received.connect(self._on_realtime_event)
        self._events_thread.start()

    def _on_realtime_event(self, event):
        event_type = event.get("type")
        dossier = get_current_dossier()
        current_id = int(dossier.get("id")) if dossier and dossier.get("id") else None
        event_dossier_id = int(event.get("dossier_id") or 0) or None

        if event_type == "dossier_changed":
            self._refresh_open_dossier_lists()
            if current_id and event_dossier_id == current_id:
                if event.get("action") == "deleted":
                    set_current_dossier(None)
                else:
                    self._reload_current_dossier(current_id)
                self.refresh_state()
            self._blink_accounting_btn_refresh(total_seconds=2)
            return

        if event_type == "accounting_changed" and current_id and event_dossier_id == current_id:
            self._refresh_child_windows()

    def _reload_current_dossier(self, dossier_id):
        try:
            response = requests.get(api_url(f"/dossiers/{dossier_id}"), timeout=10)
            response.raise_for_status()
            set_current_dossier(response.json())
        except Exception:
            pass

    def _refresh_open_dossier_lists(self):
        for window in list(self.child_windows):
            if isinstance(window, DossierListWindow):
                try:
                    window.load_dossiers()
                except Exception:
                    pass

    def _refresh_child_windows(self):
        for window in list(self.child_windows):
            for method_name in ("load_pcg", "load_journaux", "load_ecritures"):
                method = getattr(window, method_name, None)
                if callable(method):
                    try:
                        method()
                    except Exception:
                        pass

    def closeEvent(self, event):
        if getattr(self, "_events_thread", None):
            self._events_thread.stop()
            self._events_thread.wait(1000)
        super().closeEvent(event)

    # ----------------------------------------------------------------------
    #  ÉTAT DES BOUTONS
    # ----------------------------------------------------------------------
    def refresh_state(self):
        dossier = get_current_dossier()

        if dossier is None:
            self.current_dossier_label.setText("Aucun Dossier Actif")

            for btn in self.compta_buttons:
                btn.setEnabled(False)
        else:
            nom = dossier.get("nom_entreprise") or dossier.get("nom") or "Dossier sans nom"
            numero = dossier.get("num_dossier") or dossier.get("id", "")
            self.current_dossier_label.setText(f"{nom} - {numero}")
            self.current_dossier_label.setStyleSheet(
                """
                QLabel {
                    background-color: #1f6feb; /* sélection */
                    color: white;
                    border: 1px solid #174ea6;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-size: 17px;
                    font-weight: 700;
                }
                """
            )

            for btn in self.compta_buttons:
                btn.setEnabled(True)

            update_window_title(self.window(), dossier)

    def _blink_accounting_btn_refresh(self, total_seconds: int = 20):
        btn = self.btn_refresh_dossiers
        self._blink_countdown = 0

        def _toggle():
            self._blink_countdown += 1
            if self._blink_countdown % 2 == 1:
                btn.setStyleSheet(getattr(self, "_btn_refresh_dossiers_active_style", ""))
            else:
                btn.setStyleSheet(getattr(self, "_btn_refresh_dossiers_default_style", btn.styleSheet()))

            if self._blink_countdown >= 10:  # ~1s
                _blink_timer.stop()
                btn.setStyleSheet(getattr(self, "_btn_refresh_dossiers_default_style", btn.styleSheet()))

        from PySide6.QtCore import QTimer
        _blink_timer = QTimer(self)
        _blink_timer.setInterval(100)
        _blink_timer.timeout.connect(_toggle)
        _blink_timer.start()

    def _check_new_dossiers_and_blink(self):
        # évite de spam si on est déjà en train de rafraîchir
        if getattr(self, "_refresh_dossiers_in_progress", False):
            return

        try:
            # On interroge la liste des dossiers côté backend
            # (api_url est déjà importé en haut)
            r = requests.get(api_url("/dossiers/"), timeout=6)
            r.raise_for_status()
            dossiers = r.json()
            new_count = len(dossiers)
        except Exception:
            return

        if self._last_accounting_dossier_count is None:
            self._last_accounting_dossier_count = new_count
            return

        if new_count > self._last_accounting_dossier_count:
            self._last_accounting_dossier_count = new_count
            self._blink_accounting_btn_refresh()

    def refresh_dossier_list_and_select(self):
        """Rafraîchit la liste de dossiers avant de sélectionner un dossier."""

        if self._refresh_dossiers_in_progress:
            return
        self._refresh_dossiers_in_progress = True
        try:
            # On réutilise la même fenêtre liste si elle existe, sinon on l’ouvre.
            if not hasattr(self, "win_list") or not self.win_list.isVisible():
                self.open_dossier()
                return

            self.win_list.load_dossiers()
            QMessageBox.information(self, "Rafraîchi", "Liste des dossiers mise à jour.")
        finally:
            self._refresh_dossiers_in_progress = False

    def open_dossier(self):
        self.win_list = DossierListWindow()
        self.win_list.setWindowTitle("Sélectionner un dossier pour la comptabilité")
        self.win_list.btn_open.setText("Utiliser ce dossier")
        self.win_list.btn_delete.hide()
        self.win_list.btn_create.hide()
        self.win_list.btn_open.clicked.connect(self.select_accounting_dossier)
        self.win_list.table.doubleClicked.connect(lambda *_: self.select_accounting_dossier())
        self.child_windows.append(self.win_list)
        self.win_list.show()

    def selected_dossier_id_from_list(self):
        if not hasattr(self, "win_list"):
            return None

        row = self.win_list.table.currentRow()
        if row < 0:
            return None

        item = self.win_list.table.item(row, 0)
        if item is None:
            return None

        dossier_id = item.text().strip()
        return dossier_id or None

    def select_accounting_dossier(self):
        dossier_id = self.selected_dossier_id_from_list()
        if dossier_id is None:
            QMessageBox.warning(self, "Aucun dossier", "Veuillez sélectionner un dossier.")
            return

        try:
            dossier_response = requests.get(api_url(f"/dossiers/{dossier_id}"), timeout=10)
            dossier_response.raise_for_status()
            dossier = dossier_response.json()

            bootstrap_url = api_url(f"/accounting/dossiers/{dossier_id}/bootstrap")
            setup_response = requests.post(
                bootstrap_url,
                timeout=15,
            )
            setup_response.raise_for_status()
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Erreur comptable",
                f"Impossible d'ouvrir ce dossier en comptabilité : {exc}",
            )
            return

        set_current_dossier(dossier)
        self.refresh_state()
        self.win_list.close()
        QMessageBox.information(
            self,
            "Dossier sélectionné",
            f"Le dossier « {dossier.get('nom_entreprise', dossier_id)} » est maintenant actif en comptabilité.",
        )

    # ----------------------------------------------------------------------
    #  CRÉATION D’UN DOSSIER — VERSION PRO
    # ----------------------------------------------------------------------
    def create_dossier(self):
        self.win_create = DossierCreateDialog(self)
        if self.win_create.exec():
            self.refresh_state()
            self._blink_accounting_btn_refresh(total_seconds=20)

    # ----------------------------------------------------------------------
    #  MODIFICATION (à venir)
    # ----------------------------------------------------------------------
    def modify_dossier(self):
        dossier = get_current_dossier()
        if dossier is None:
            QMessageBox.warning(self, "Erreur", "Sélectionnez d'abord un dossier.")
            return

        self.win_modify = DossierCreateDialog(self, dossier_id=dossier["id"])
        if self.win_modify.exec():
            try:
                response = requests.get(api_url(f"/dossiers/{dossier['id']}"), timeout=10)
                response.raise_for_status()
                set_current_dossier(response.json())
            except Exception:
                pass
            self.refresh_state()

    # ----------------------------------------------------------------------
    #  SUPPRESSION
    # ----------------------------------------------------------------------
    def delete_dossier(self):
        delete_dossier_with_alerts(self)
        self.refresh_state()
        self._blink_accounting_btn_refresh(total_seconds=20)

    # ----------------------------------------------------------------------
    #  TABLEAU DE BORD COMPTABLE 2026
    # ----------------------------------------------------------------------
    def open_dashboard_2026(self):
        self.win_dashboard_2026 = Accounting2026Dashboard()
        self.child_windows.append(self.win_dashboard_2026)
        self.win_dashboard_2026.show()


    # ----------------------------------------------------------------------
    #  PLAN COMPTABLE
    # ----------------------------------------------------------------------
    def open_pcg(self):
        dossier = get_current_dossier()
        if dossier is None:
            QMessageBox.warning(self, "Erreur", "Aucun dossier n'est ouvert.")
            return

        win = PCGListWindow(dossier["id"])
        self.child_windows.append(win)
        win.show()

    # ----------------------------------------------------------------------
    #  OUVERTURE GÉNÉRIQUE
    # ----------------------------------------------------------------------
    def open_window(self, window_class):
        dossier = get_current_dossier()
        try:
            win = window_class(dossier["id"]) if dossier else window_class()
        except TypeError:
            win = window_class()
        self.child_windows.append(win)
        win.show()

    # ----------------------------------------------------------------------
    #  NON IMPLÉMENTÉ
    # ----------------------------------------------------------------------
    def not_implemented(self):
        QMessageBox.information(self, "Info", "Fonctionnalité disponible à l’étape 2.")
