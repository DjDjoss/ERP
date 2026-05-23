# main.py
# -*- coding: utf-8 -*-

import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QProgressBar, QTabWidget, QHBoxLayout
)
from PySide6.QtCore import Qt, QThread, Signal

# Orchestrateur (backend + PostgreSQL)
from erp_orchestrator import orchestrate, memory_handler

# Tes modules ERP
from modules.accounting.views import AccountingModule
from modules.dossiers.views import DossiersModule


# ============================================================
# THREAD D’ORCHESTRATION (NE BLOQUE PAS L’UI)
# ============================================================

class OrchestratorThread(QThread):
    progress = Signal(int)
    message = Signal(str)
    finished_ok = Signal(bool)

    def __init__(self, dev_mode=True):
        super().__init__()
        self.dev_mode = dev_mode

    def run(self):
        ok = orchestrate(
            dev_mode=self.dev_mode,
            progress_cb=lambda p: self.progress.emit(p),
            message_cb=lambda m: self.message.emit(m),
        )
        self.finished_ok.emit(ok)


# ============================================================
# SPLASHSCREEN PRO
# ============================================================

class SplashWindow(QWidget):
    def __init__(self, dev_mode=True):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(500, 220)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.logo_label = QLabel("ERP Rosan")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #333;")

        self.info_label = QLabel("Initialisation…")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 13px; color: #555;")

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #aaa;
                border-radius: 4px;
                height: 18px;
                text-align: center;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #2d7dd2;
                border-radius: 4px;
            }
        """)

        self.log_label = QLabel("")
        self.log_label.setAlignment(Qt.AlignCenter)
        self.log_label.setStyleSheet("font-size: 11px; color: #777;")
        self.log_label.setWordWrap(True)

        layout.addWidget(self.logo_label)
        layout.addWidget(self.info_label)
        layout.addWidget(self.progress)
        layout.addWidget(self.log_label)

        self.setLayout(layout)

        self.thread = OrchestratorThread(dev_mode=dev_mode)
        self.thread.progress.connect(self.on_progress)
        self.thread.message.connect(self.on_message)
        self.thread.finished_ok.connect(self.on_finished)
        self.thread.start()

        self.startTimer(400)

    def timerEvent(self, event):
        if memory_handler.records:
            self.log_label.setText(memory_handler.records[-1])

    def on_progress(self, value):
        self.progress.setValue(value)

    def on_message(self, msg):
        self.info_label.setText(msg)

    def on_finished(self, ok):
        if ok:
            self.info_label.setText("Démarrage terminé. Ouverture de l’ERP…")
        else:
            self.info_label.setText("Erreur au démarrage. Voir les logs.")
        self.thread.msleep(700)
        self.close()
        self.parent().show_main_window(ok)


# ============================================================
# VRAIE FENÊTRE ERP (onglets Dossiers + Comptabilité)
# ============================================================

class ERPMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ERP Rosan – Architecture Modulaire")
        self.resize(1400, 900)

        central = QWidget()
        central_layout = QVBoxLayout()
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central.setLayout(central_layout)
        self.setCentralWidget(central)

        header = QWidget()
        header.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-bottom: 1px solid #d7dde8;
            }
            QLabel#appTitle {
                color: #1f2937;
                font-size: 24px;
                font-weight: 800;
                padding: 12px 6px 12px 16px;
            }
            QLabel#moduleTitle {
                color: #174ea6;
                font-size: 20px;
                font-weight: 700;
                padding: 14px 16px 12px 0;
            }
        """)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)
        header.setLayout(header_layout)

        self.app_title_label = QLabel("ERP Rosan")
        self.app_title_label.setObjectName("appTitle")
        self.module_title_label = QLabel("")
        self.module_title_label.setObjectName("moduleTitle")

        header_layout.addWidget(self.app_title_label, 0, Qt.AlignVCenter)
        header_layout.addWidget(self.module_title_label, 0, Qt.AlignVCenter)
        header_layout.addStretch(1)

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.update_module_title)

        central_layout.addWidget(header)
        central_layout.addWidget(self.tabs)

        self.load_modules()
        self.update_module_title(self.tabs.currentIndex())

    def load_modules(self):
        self.load_dossiers_module()
        self.load_accounting_module()

    def load_dossiers_module(self):
        import modules.dossiers.ui.dossier_list_window as dlw
        print(">>> DOSSIER LIST WINDOW CHARGÉ DEPUIS :", dlw.__file__)

        dossiers_widget = DossiersModule()
        self.tabs.addTab(dossiers_widget, "Dossiers")

    def load_accounting_module(self):
        accounting_widget = AccountingModule()
        self.tabs.addTab(accounting_widget, "Comptabilité")

    def update_module_title(self, index):
        if index < 0:
            self.module_title_label.setText("")
            return

        tab_name = self.tabs.tabText(index)
        if tab_name == "Comptabilité":
            self.module_title_label.setText("Module Comptabilité")
        else:
            self.module_title_label.setText(tab_name)


# ============================================================
# ROOT WRAPPER (SPLASH → ERP)
# ============================================================

class RootApp(QWidget):
    def __init__(self, dev_mode=True):
        super().__init__()
        self.dev_mode = dev_mode
        self.main_window = None

        self.splash = SplashWindow(dev_mode=self.dev_mode)
        self.splash.setParent(self)
        self.splash.show()

    def show_main_window(self, ok):
        if ok:
            self.main_window = ERPMainWindow()
            self.main_window.show()
        else:
            sys.exit(1)


# ============================================================
# MAIN
# ============================================================

def main():
    print(">>> MAIN.PY EXÉCUTÉ DEPUIS :", os.path.abspath(__file__))

    app = QApplication(sys.argv)

    # Shutdown propre: arrêter le backend Uvicorn démarré par l’orchestrateur
    # quand l’utilisateur ferme définitivement l’ERP.
    try:
        from erp_orchestrator import shutdown_backend

        def _on_about_to_quit():
            shutdown_backend()

        app.aboutToQuit.connect(_on_about_to_quit)
    except Exception:
        pass

    dev_mode = True
    root = RootApp(dev_mode=dev_mode)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
