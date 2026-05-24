# -*- coding: utf-8 -*-
"""
Interface principale du module Comptabilité avec onglets
Refactorisation complète pour une navigation moderne type Sage/Odoo
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, 
    QPushButton, QLabel, QHBoxLayout, QStatusBar,
    QMessageBox, QToolBar, QAction, QMenuBar, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont

from modules.accounting.dossier_open import DossierOpenDialog
from modules.accounting.ecriture_saisie import EcritureSaisieWindow
from modules.accounting.ecritures_list import EcrituresListWindow
from modules.accounting.journaux_list import JournauxListWindow
from modules.accounting.journaux_create import JournauxCreateWindow
from modules.accounting.pcg_list import PCGListWindow
from modules.accounting.client_list import ClientListWindow
from modules.accounting.fournisseur_list import FournisseurListWindow
from modules.accounting.accounting_reports import AccountingReportsWindow
from modules.accounting.accounting_2026_dashboard import DashboardWindow


class AccountingMainWindow(QMainWindow):
    """Fenêtre principale du module comptable avec navigation par onglets"""
    
    dossier_changed = Signal(int)  # Signal émis quand un dossier est ouvert
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.dossier_id = None
        self.dossier_nom = ""
        self.dossier_db_name = ""
        
        self.setWindowTitle("Djoss ERP - Module Comptabilité")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #2196F3;
            }
            QTabBar::tab:hover {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QLabel#titre {
                font-size: 24px;
                font-weight: bold;
                color: #333;
            }
            QLabel#sous_titre {
                font-size: 14px;
                color: #666;
            }
        """)
        
        self._init_ui()
        self._init_menu()
        self._init_toolbar()
        self._init_statusbar()
        
    def _init_ui(self):
        """Initialise l'interface utilisateur avec onglets"""
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        
        layout_principal = QVBoxLayout(widget_central)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(15)
        
        # En-tête avec titre et bouton ouvrir dossier
        header_layout = QHBoxLayout()
        
        titre_label = QLabel("📊 Module Comptabilité")
        titre_label.setObjectName("titre")
        header_layout.addWidget(titre_label)
        
        header_layout.addStretch()
        
        self.lbl_dossier_actuel = QLabel("Aucun dossier ouvert")
        self.lbl_dossier_actuel.setObjectName("sous_titre")
        header_layout.addWidget(self.lbl_dossier_actuel)
        
        btn_ouvrir = QPushButton("📁 Ouvrir un dossier")
        btn_ouvrir.clicked.connect(self.ouvrir_dossier)
        header_layout.addWidget(btn_ouvrir)
        
        layout_principal.addLayout(header_layout)
        
        # Widget à onglets
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)
        self.tabs.setIconSize(Qt.Size(20, 20))
        
        # Onglet 1 : Tableau de bord
        self.tab_dashboard = QWidget()
        self.tabs.addTab(self.tab_dashboard, "📈 Tableau de bord")
        self._setup_dashboard_tab()
        
        # Onglet 2 : Saisie des écritures
        self.tab_saisie = QWidget()
        self.tabs.addTab(self.tab_saisie, "✏️ Saisie des écritures")
        self._setup_saisie_tab()
        
        # Onglet 3 : Consultation des écritures
        self.tab_consultation = QWidget()
        self.tabs.addTab(self.tab_consultation, "📋 Consultation des écritures")
        self._setup_consultation_tab()
        
        # Onglet 4 : Journaux
        self.tab_journaux = QWidget()
        self.tabs.addTab(self.tab_journaux, "📚 Journaux")
        self._setup_journaux_tab()
        
        # Onglet 5 : Plan comptable
        self.tab_pcg = QWidget()
        self.tabs.addTab(self.tab_pcg, "📖 Plan comptable")
        self._setup_pcg_tab()
        
        # Onglet 6 : Tiers (Clients/Fournisseurs)
        self.tab_tiers = QWidget()
        self.tabs.addTab(self.tab_tiers, "👥 Tiers")
        self._setup_tiers_tab()
        
        # Onglet 7 : États et rapports
        self.tab_rapports = QWidget()
        self.tabs.addTab(self.tab_rapports, "📊 États et rapports")
        self._setup_rapports_tab()
        
        layout_principal.addWidget(self.tabs)
        
        # Désactiver tous les onglets tant qu'aucun dossier n'est ouvert
        self._desactiver_onglets()
        
    def _setup_dashboard_tab(self):
        """Configure l'onglet Tableau de bord"""
        layout = QVBoxLayout(self.tab_dashboard)
        layout.setAlignment(Qt.AlignCenter)
        
        label = QLabel("📈 Tableau de bord comptable\n\nSélectionnez un dossier pour afficher les indicateurs")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: #666;")
        layout.addWidget(label)
        
        self.dashboard_widget = None
        
    def _setup_saisie_tab(self):
        """Configure l'onglet Saisie des écritures"""
        layout = QVBoxLayout(self.tab_saisie)
        layout.setAlignment(Qt.AlignCenter)
        
        container = QWidget()
        container.setMaximumWidth(600)
        container_layout = QVBoxLayout(container)
        
        titre = QLabel("✏️ Saisie d'une nouvelle écriture")
        titre.setStyleSheet("font-size: 18px; font-weight: bold;")
        titre.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(titre)
        
        btn_saisir = QPushButton("➕ Nouvelle écriture")
        btn_saisir.setMinimumHeight(50)
        btn_saisir.setStyleSheet("font-size: 16px;")
        btn_saisir.clicked.connect(self.nouvelle_ecriture)
        container_layout.addWidget(btn_saisir)
        
        info = QLabel("Cliquez pour saisir une nouvelle écriture comptable")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #999;")
        container_layout.addWidget(info)
        
        layout.addWidget(container)
        
    def _setup_consultation_tab(self):
        """Configure l'onglet Consultation des écritures"""
        layout = QVBoxLayout(self.tab_consultation)
        
        btn_consulter = QPushButton("📋 Consulter toutes les écritures")
        btn_consulter.setMinimumHeight(50)
        btn_consulter.setStyleSheet("font-size: 16px;")
        btn_consulter.clicked.connect(self.consulter_ecritures)
        layout.addWidget(btn_consulter)
        
    def _setup_journaux_tab(self):
        """Configure l'onglet Journaux"""
        layout = QVBoxLayout(self.tab_journaux)
        layout.setSpacing(15)
        
        titre = QLabel("📚 Gestion des journaux comptables")
        titre.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(titre)
        
        btn_liste = QPushButton("📋 Liste des journaux")
        btn_liste.setMinimumHeight(45)
        btn_liste.clicked.connect(self.voir_journaux)
        layout.addWidget(btn_liste)
        
        btn_creer = QPushButton("➕ Créer un journal")
        btn_creer.setMinimumHeight(45)
        btn_creer.clicked.connect(self.creer_journal)
        layout.addWidget(btn_creer)
        
        layout.addStretch()
        
    def _setup_pcg_tab(self):
        """Configure l'onglet Plan comptable"""
        layout = QVBoxLayout(self.tab_pcg)
        
        btn_pcg = QPushButton("📖 Consulter le plan comptable")
        btn_pcg.setMinimumHeight(50)
        btn_pcg.setStyleSheet("font-size: 16px;")
        btn_pcg.clicked.connect(self.voir_pcg)
        layout.addWidget(btn_pcg)
        
    def _setup_tiers_tab(self):
        """Configure l'onglet Tiers"""
        layout = QVBoxLayout(self.tab_tiers)
        layout.setSpacing(15)
        
        titre = QLabel("👥 Gestion des tiers")
        titre.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(titre)
        
        btn_clients = QPushButton("🏢 Clients")
        btn_clients.setMinimumHeight(45)
        btn_clients.clicked.connect(self.voir_clients)
        layout.addWidget(btn_clients)
        
        btn_fournisseurs = QPushButton("🚚 Fournisseurs")
        btn_fournisseurs.setMinimumHeight(45)
        btn_fournisseurs.clicked.connect(self.voir_fournisseurs)
        layout.addWidget(btn_fournisseurs)
        
        layout.addStretch()
        
    def _setup_rapports_tab(self):
        """Configure l'onglet États et rapports"""
        layout = QVBoxLayout(self.tab_rapports)
        
        btn_rapports = QPushButton("📊 Générer les états comptables")
        btn_rapports.setMinimumHeight(50)
        btn_rapports.setStyleSheet("font-size: 16px;")
        btn_rapports.clicked.connect(self.generer_rapports)
        layout.addWidget(btn_rapports)
        
    def _init_menu(self):
        """Initialise la barre de menu"""
        menubar = self.menuBar()
        
        # Menu Fichier
        menu_fichier = menubar.addMenu("&Fichier")
        
        action_ouvrir = QAction("📁 Ouvrir un dossier", self)
        action_ouvrir.triggered.connect(self.ouvrir_dossier)
        menu_fichier.addAction(action_ouvrir)
        
        menu_fichier.addSeparator()
        
        action_quitter = QAction("❌ Quitter", self)
        action_quitter.triggered.connect(self.close)
        menu_fichier.addAction(action_quitter)
        
        # Menu Édition
        menu_edition = menubar.addMenu("É&dition")
        
        action_ecriture = QAction("✏️ Nouvelle écriture", self)
        action_ecriture.triggered.connect(self.nouvelle_ecriture)
        menu_edition.addAction(action_ecriture)
        
        # Menu Aide
        menu_aide = menubar.addMenu("&?")
        
        action_info = QAction("ℹ️ À propos", self)
        action_info.triggered.connect(self.a_propos)
        menu_aide.addAction(action_info)
        
    def _init_toolbar(self):
        """Initialise la barre d'outils"""
        toolbar = QToolBar("Barre principale")
        toolbar.setMovable(False)
        toolbar.setIconSize(Qt.Size(24, 24))
        self.addToolBar(toolbar)
        
        action_ouvrir = QAction("📁 Ouvrir", self)
        action_ouvrir.setToolTip("Ouvrir un dossier comptable")
        action_ouvrir.triggered.connect(self.ouvrir_dossier)
        toolbar.addAction(action_ouvrir)
        
        toolbar.addSeparator()
        
        action_saisie = QAction("✏️ Saisie", self)
        action_saisie.setToolTip("Saisir une écriture")
        action_saisie.triggered.connect(self.nouvelle_ecriture)
        toolbar.addAction(action_saisie)
        
        action_consultation = QAction("📋 Consultation", self)
        action_consultation.setToolTip("Consulter les écritures")
        action_consultation.triggered.connect(self.consulter_ecritures)
        toolbar.addAction(action_consultation)
        
    def _init_statusbar(self):
        """Initialise la barre de statut"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Prêt - Veuillez ouvrir un dossier comptable")
        
    def _desactiver_onglets(self):
        """Désactive tous les onglets sauf le tableau de bord"""
        for i in range(1, self.tabs.count()):
            self.tabs.setTabEnabled(i, False)
            
    def _activer_onglets(self):
        """Active tous les onglets"""
        for i in range(self.tabs.count()):
            self.tabs.setTabEnabled(i, True)
        
    def ouvrir_dossier(self):
        """Ouvre le dialog de sélection de dossier"""
        dialog = DossierOpenDialog(self)
        if dialog.exec():
            dossier_data = dialog.get_selected_dossier()
            if dossier_data:
                self.dossier_id = dossier_data['id']
                self.dossier_nom = dossier_data['nom']
                self.dossier_db_name = dossier_data.get('db_name', f"dossier_{self.dossier_id}")
                
                self.lbl_dossier_actuel.setText(f"Dossier : {self.dossier_nom}")
                self.statusbar.showMessage(f"Dossier '{self.dossier_nom}' ouvert avec succès")
                
                self._activer_onglets()
                self.dossier_changed.emit(self.dossier_id)
                
                # Charger le dashboard
                self._charger_dashboard()
                
    def _charger_dashboard(self):
        """Charge le tableau de bord pour le dossier actuel"""
        if self.dashboard_widget:
            self.dashboard_widget.deleteLater()
            
        if self.dossier_id:
            self.dashboard_widget = DashboardWindow(self.dossier_id)
            layout = QVBoxLayout(self.tab_dashboard)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.dashboard_widget)
            
    def nouvelle_ecriture(self):
        """Ouvre la fenêtre de saisie d'écriture"""
        if not self.dossier_id:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord ouvrir un dossier comptable.")
            return
            
        fenetre = EcritureSaisieWindow(self.dossier_id, self.dossier_db_name)
        fenetre.exec()
        
    def consulter_ecritures(self):
        """Ouvre la fenêtre de consultation des écritures"""
        if not self.dossier_id:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord ouvrir un dossier comptable.")
            return
            
        fenetre = EcrituresListWindow(self.dossier_id, self.dossier_db_name)
        fenetre.exec()
        
    def voir_journaux(self):
        """Ouvre la liste des journaux"""
        if not self.dossier_id:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord ouvrir un dossier comptable.")
            return
            
        fenetre = JournauxListWindow(self.dossier_id, self.dossier_db_name)
        fenetre.exec()
        
    def creer_journal(self):
        """Ouvre la fenêtre de création de journal"""
        if not self.dossier_id:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord ouvrir un dossier comptable.")
            return
            
        fenetre = JournauxCreateWindow(self.dossier_id, self.dossier_db_name)
        fenetre.exec()
        
    def voir_pcg(self):
        """Ouvre la liste du plan comptable"""
        if not self.dossier_id:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord ouvrir un dossier comptable.")
            return
            
        fenetre = PCGListWindow(self.dossier_id, self.dossier_db_name)
        fenetre.exec()
        
    def voir_clients(self):
        """Ouvre la liste des clients"""
        if not self.dossier_id:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord ouvrir un dossier comptable.")
            return
            
        fenetre = ClientListWindow(self.dossier_id, self.dossier_db_name)
        fenetre.exec()
        
    def voir_fournisseurs(self):
        """Ouvre la liste des fournisseurs"""
        if not self.dossier_id:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord ouvrir un dossier comptable.")
            return
            
        fenetre = FournisseurListWindow(self.dossier_id, self.dossier_db_name)
        fenetre.exec()
        
    def generer_rapports(self):
        """Ouvre la fenêtre des rapports comptables"""
        if not self.dossier_id:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord ouvrir un dossier comptable.")
            return
            
        fenetre = AccountingReportsWindow(self.dossier_id, self.dossier_db_name)
        fenetre.exec()
        
    def a_propos(self):
        """Affiche la boîte de dialogue À propos"""
        QMessageBox.information(
            self,
            "À propos de Djoss ERP",
            "Module Comptabilité v2.0\n\n"
            "Développé avec ❤️ pour les experts-comptables\n"
            "Compatible PCG Français\n\n"
            "Fonctionnalités :\n"
            "• Saisie des écritures\n"
            "• Balance générale\n"
            "• Grand livre\n"
            "• Balance âgée\n"
            "• Export FEC\n"
            "• Comptabilité analytique\n"
            "• Trésorerie\n"
            "• Immobilisations"
        )


def launch_accounting_module():
    """Point d'entrée pour lancer le module comptable"""
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    fenetre = AccountingMainWindow()
    fenetre.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_accounting_module()
