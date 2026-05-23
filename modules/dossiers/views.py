# ============================================================
#  MODULE DOSSIERS — GESTION LISTE / CRÉATION / MODIFICATION
#  Ce fichier gère :
#   ✔ l’ouverture de la fenêtre de création
#   ✔ l’ouverture de la fenêtre de modification
#   ✔ la suppression (avec 4 confirmations)
#   ✔ le rechargement automatique de la liste
# ============================================================

import requests
from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PySide6.QtCore import QTimer
from modules.config import api_url
from modules.realtime_events import RealtimeEventsThread


from modules.dossiers.ui.dossier_list_window import DossierListWindow
from modules.dossiers.dossier_create_dialog import DossierCreateDialog

API_URL = api_url("/dossiers")


class DossiersModule(QWidget):
    def __init__(self):
        super().__init__()

        # Indique si un rafraîchissement a été demandé
        self.refresh_dossiers_pending = False


        # ------------------------------------------------------------
        # 1) Mise en place du layout principal
        # ------------------------------------------------------------
        layout = QVBoxLayout()
        self.setLayout(layout)

        # ------------------------------------------------------------
        # 2) Chargement de la fenêtre liste des dossiers
        # ------------------------------------------------------------
        self.table_window = DossierListWindow()
        layout.addWidget(self.table_window)

        # ------------------------------------------------------------
        # 3) Sécurisation : on déconnecte les signaux existants
        #    (évite les doublons si la fenêtre est rechargée)
        # ------------------------------------------------------------
        # Ne pas faire disconnect() sans slots : PySide peut lever un warning
        for btn in (
            self.table_window.btn_create,
            self.table_window.btn_delete,
            self.table_window.btn_open,
        ):
            try:
                btn.clicked.disconnect()
            except (TypeError, RuntimeError):
                pass

        # ------------------------------------------------------------
        # 4) Connexions des boutons
        # ------------------------------------------------------------
        self.table_window.btn_create.clicked.connect(self.open_create_window)
        self.table_window.btn_delete.clicked.connect(self.delete_selected_dossier)
        self.table_window.btn_open.clicked.connect(self.modify_selected_dossier)

        # Rafraîchir (liste dossiers)
        if hasattr(self.table_window, "btn_refresh"):
            self.table_window.btn_refresh.clicked.connect(self.refresh_dossiers)
            self.refresh_dossiers_pending = False
            # Style "clignotement" à la détection d'une nouvelle entrée (option visuelle)
            self._btn_refresh_blink_timer = None


        self.table_window.table.doubleClicked.connect(self.modify_selected_dossier)

        # --- Clignotement du bouton rafraîchir quand une nouvelle entrée apparaît ---
        # Principe: on mémorise l'ID/compteur initial et on poll une fois toutes les N secondes.
        # Si un nouveau dossier apparaît côté backend, on fait clignoter le bouton.
        self._last_dossier_count = None
        self._blink_countdown = 0

        if hasattr(self.table_window, "btn_refresh"):
            self._refresh_blink_timer = QTimer(self)
            self._refresh_blink_timer.setInterval(300000)  # 5 minutes de polling

            self._refresh_blink_timer.timeout.connect(self._check_new_dossiers_and_blink)
            self._refresh_blink_timer.start()

        # Initialisation de la référence (sans clignotement)
        try:
            self._last_dossier_count = self.table_window.table.rowCount()
        except Exception:
            self._last_dossier_count = None

        self._events_thread = RealtimeEventsThread(self)
        self._events_thread.event_received.connect(self._on_realtime_event)
        self._events_thread.start()

    def _on_realtime_event(self, event):
        if event.get("type") != "dossier_changed":
            return

        try:
            self.table_window.load_dossiers()
            self._last_dossier_count = self.table_window.table.rowCount()
        except Exception:
            return

    def closeEvent(self, event):
        if getattr(self, "_events_thread", None):
            self._events_thread.stop()
            self._events_thread.wait(1000)
        super().closeEvent(event)

    def _check_new_dossiers_and_blink(self):
        if not hasattr(self.table_window, "btn_refresh"):
            return

        # évite de spam si on est déjà en train de rafraîchir
        if getattr(self, "refresh_dossiers_pending", False):
            return

        try:
            r = requests.get(API_URL, timeout=6)
            r.raise_for_status()
            dossiers = r.json()
            new_count = len(dossiers)
        except Exception:
            return

        if self._last_dossier_count is None:
            self._last_dossier_count = new_count
            return

        if new_count > self._last_dossier_count:
            self._last_dossier_count = new_count
            # clignotement périodique (lorsqu'un autre utilisateur ajoute)
            self._blink_btn_refresh(total_seconds=20)


    def _blink_btn_refresh(self, total_seconds: int = 20):
        """Fait clignoter le bouton Rafraîchir pendant ~20s.

        total_seconds: durée totale du clignotement.
        """
        btn = self.table_window.btn_refresh

        # Evite de lancer plusieurs timers concurrents
        if getattr(self, "_blink_timer", None):
            try:
                self._blink_timer.stop()
            except Exception:
                pass

        # interval 100ms => 10 toggles par seconde
        interval_ms = 100
        max_ticks = max(1, int((total_seconds * 1000) / interval_ms))

        self._blink_countdown = 0

        def _toggle():
            self._blink_countdown += 1
            if self._blink_countdown % 2 == 1:
                btn.setStyleSheet(getattr(self.table_window, "_btn_refresh_active_style", ""))
            else:
                btn.setStyleSheet(
                    getattr(self.table_window, "_btn_refresh_default_style", btn.styleSheet())
                )

            if self._blink_countdown >= max_ticks:
                try:
                    self._blink_timer.stop()
                except Exception:
                    pass
                btn.setStyleSheet(
                    getattr(self.table_window, "_btn_refresh_default_style", btn.styleSheet())
                )

        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(interval_ms)
        self._blink_timer.timeout.connect(_toggle)
        self._blink_timer.start()



    def refresh_dossiers(self):

        """Rafraîchit la liste des dossiers (utile si un autre utilisateur a modifié)."""
        self.refresh_dossiers_pending = True
        if hasattr(self.table_window, "btn_refresh"):
            # Mettre le bouton en rouge pendant l'action
            self.table_window.btn_refresh.setStyleSheet(
                getattr(self.table_window, "_btn_refresh_active_style", self.table_window.btn_refresh.styleSheet())
            )
            self.table_window.btn_refresh.setEnabled(False)

        try:
            self.table_window.load_dossiers()
            QMessageBox.information(self, "Rafraîchi", "Liste des dossiers mise à jour.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de rafraîchir : {e}")
        finally:
            self.refresh_dossiers_pending = False
            if hasattr(self.table_window, "btn_refresh"):
                self.table_window.btn_refresh.setStyleSheet(
                    getattr(self.table_window, "_btn_refresh_default_style", self.table_window.btn_refresh.styleSheet())
                )
                self.table_window.btn_refresh.setEnabled(True)

    def selected_dossier_id(self):

        row = self.table_window.table.currentRow()
        if row < 0:
            return None

        item = self.table_window.table.item(row, 0)
        if item is None:
            return None

        return item.text().strip()

    def api_error_message(self, response):
        try:
            payload = response.json()
        except ValueError:
            return response.text

        if isinstance(payload, dict) and payload.get("detail"):
            return str(payload["detail"])
        return response.text

    # ============================================================
    #  CRÉATION D’UN DOSSIER
    # ============================================================
    def open_create_window(self):
        """
        Ouvre la fenêtre de création d’un dossier.
        """
        dialog = DossierCreateDialog(self, dossier_id=None)
        if dialog.exec():
            self.table_window.load_dossiers()
            if hasattr(self.table_window, "btn_refresh"):
                self._blink_btn_refresh(total_seconds=20)

    # ============================================================
    #  MODIFICATION D’UN DOSSIER
    # ============================================================
    def modify_selected_dossier(self):
        """
        Ouvre la fenêtre de modification pour le dossier sélectionné.
        """
        dossier_id = self.selected_dossier_id()
        if dossier_id is None:
            QMessageBox.warning(self, "Aucun dossier", "Veuillez sélectionner un dossier.")
            return

        dialog = DossierCreateDialog(self, dossier_id=dossier_id)
        if dialog.exec():
            self.table_window.load_dossiers()
            if hasattr(self.table_window, "btn_refresh"):
                self._blink_btn_refresh(total_seconds=20)

    # ============================================================
    #  SUPPRESSION D’UN DOSSIER (4 CONFIRMATIONS)
    # ============================================================
    def delete_selected_dossier(self):
        """
        Supprime un dossier après 4 confirmations successives.
        """
        dossier_id = self.selected_dossier_id()
        if dossier_id is None:
            QMessageBox.warning(self, "Aucun dossier", "Veuillez sélectionner un dossier.")
            return

        # 4 alertes successives
        alerts = [
            "Êtes-vous absolument sûr de vouloir supprimer ce dossier ?",
            "Cette action est irréversible. Vous confirmez ?",
            "Dernière vérification : supprimer définitivement ?",
            "C’est votre dernière chance d’annuler. Supprimer ?"
        ]

        for msg in alerts:
            confirm = QMessageBox.question(
                self,
                "Confirmation",
                msg,
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm != QMessageBox.Yes:
                return  # Annulation immédiate

        # ------------------------------------------------------------
        # Suppression API
        # ------------------------------------------------------------
        try:
            response = requests.delete(f"{API_URL}{dossier_id}", timeout=10)
            if not response.ok:
                raise RuntimeError(self.api_error_message(response))

            QMessageBox.information(self, "Succès", "Dossier supprimé.")
            self.table_window.load_dossiers()
            if hasattr(self.table_window, "btn_refresh"):
                self._blink_btn_refresh(total_seconds=20)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de supprimer : {e}")
