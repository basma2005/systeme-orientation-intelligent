from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QHBoxLayout, QTabWidget, QHeaderView,
    QFrame, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont, QColor, QIcon
from PyQt5.QtCore import Qt, QTimer
import requests
from datetime import datetime
import json
import logging
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class AdvisorDashboard(QWidget):
    return_to_login_signal = pyqtSignal()

    def __init__(self, db, login_window=None, api_url="http://localhost:5000"):
        super().__init__()
        self.db = db
        self.api_url = api_url
        self.setWindowTitle("Tableau de bord - Conseiller en Orientation")
        self.setWindowIcon(QIcon("ressources/images/icon.png"))
        self.setMinimumSize(1200, 800)

        self.login_window = login_window

        self.init_ui()
        self.setup_auto_refresh()
        self.load_data()
        
        # Style global de l'application
        self.setStyleSheet(f"""
            QWidget {{
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QLineEdit {{
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 8px;
                min-height: 30px;
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(72,171,214,255);
            }}
        """)

    def init_ui(self):
        # Disposition principale
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Création de la barre d'en-tête
        self.create_header_bar(main_layout)

        # Zone de contenu principale
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_widget.setStyleSheet("""
            #contentWidget {
                background-color: #f5f7fa;
            }
        """)
        main_layout.addWidget(content_widget)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        content_widget.setLayout(content_layout)

        # Titre du tableau de bord
        dashboard_title = QLabel("🎯 Conseiller les étudiants")
        dashboard_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        dashboard_title.setStyleSheet("color: rgba(0,84,123,255); margin-bottom: 10px;")
        content_layout.addWidget(dashboard_title)

        # Barre de statut
        self.status_bar = QLabel()
        self.status_bar.setFont(QFont("Segoe UI", 9))
        self.status_bar.setStyleSheet("color: #7f8c8d;")
        self.update_status("🟢 Système prêt")
        content_layout.addWidget(self.status_bar)

        # Onglets
        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                margin-top: 10px;
                background: white;
            }}
            QTabBar::tab {{
                background: #ecf0f1;
                border: 1px solid #d0d0d0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 16px;
                margin-right: 4px;
                color: rgba(0,84,123,255);
            }}
            QTabBar::tab:selected {{
                background: white;
                border-bottom: 2px solid rgba(72,171,214,255);
                color: rgba(72,171,214,255);
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background: rgba(72,171,214,40);
            }}
        """)
        content_layout.addWidget(self.tabs)

        # Initialisation des onglets
        self.init_class_tab()
        self.init_student_tab()
        self.init_stats_tab()

        # Bouton de réinitialisation
        reset_btn = QPushButton("🔁 Réinitialiser toutes les données (Fin d'accompagnement)")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(238,116,2,255);
                color: white;
                padding: 12px;
                border-radius: 4px;
                border: none;
                font-weight: bold;
                margin-top: 20px;
            }}
            QPushButton:hover {{
                background-color: rgba(238,116,2,200);
            }}
            QPushButton:pressed {{
                background-color: rgba(238,116,2,150);
            }}
        """)
        reset_btn.clicked.connect(self.confirm_reset_data)
        content_layout.addWidget(reset_btn)

    def create_header_bar(self, parent_layout):
        """Crée une barre d'en-tête moderne"""
        header = QWidget()
        header.setObjectName("header")
        header.setStyleSheet(f"""
            #header {{
                background-color: rgba(72,171,214,255);
                border-bottom: 1px solid rgba(0,84,123,255);
            }}
        """)
        header.setFixedHeight(60)
        parent_layout.addWidget(header)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 0, 20, 0)
        header.setLayout(header_layout)

        # Logo et titre
        logo_title = QHBoxLayout()
        logo_title.setSpacing(10)
    
        logo_label = QLabel("")
        logo_label.setFont(QFont("Segoe UI", 24))
        logo_title.addWidget(logo_label)
    
        title = QLabel("Conseiller d'Orientation")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: white;")
        logo_title.addWidget(title)
    
        header_layout.addLayout(logo_title)

        # Espaceur
        header_layout.addStretch()

        # Bouton de retour
        return_btn = QPushButton("🔙 Retour à la connexion")
        return_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                border: 1px solid white;
                min-width: 120px;
                margin-right: 15px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
        """)
        return_btn.clicked.connect(self.return_to_login)
        header_layout.addWidget(return_btn)

        # Info utilisateur
        user_info = QHBoxLayout()
        user_info.setSpacing(10)
    
        user_icon = QLabel("👤")
        user_icon.setFont(QFont("Segoe UI", 16))
        user_info.addWidget(user_icon)
    
        user_name = QLabel("Conseiller")
        user_name.setFont(QFont("Segoe UI", 10))
        user_name.setStyleSheet("color: white;")
        user_info.addWidget(user_name)
    
        header_layout.addLayout(user_info)

    def return_to_login(self):
        """Gère le retour à la page de connexion"""
        reply = QMessageBox.question(
            self, 
            'Confirmer l\'action', 
            'Êtes-vous sûr de vouloir retourner à la page de connexion?',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
    
        if reply == QMessageBox.Yes:
            self.return_to_login_signal.emit()
            self.close()

    def init_class_tab(self):
        """Onglet de gestion des classes"""
        self.class_tab = QWidget()
        self.tabs.addTab(self.class_tab, "📚 Classes")

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        self.class_tab.setLayout(layout)

        # Titre de section
        section_title = QLabel("🏫 Gestion des Classes")
        section_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        section_title.setStyleSheet("color: rgba(0,84,123,255); margin-bottom: 10px;")
        layout.addWidget(section_title)

        # Formulaire
        form_card = QWidget()
        form_card.setObjectName("formCard")
        form_card.setStyleSheet("""
            #formCard {
                background-color: white;
                border-radius: 6px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        form_layout = QHBoxLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(15)
        form_card.setLayout(form_layout)

        # Champs de formulaire
        self.class_name_input = QLineEdit()
        self.class_name_input.setPlaceholderText("Nom de la classe")
        self.class_name_input.setMinimumWidth(200)
        
        self.class_code_input = QLineEdit()
        self.class_code_input.setPlaceholderText("Code d'accès")
        self.class_code_input.setMinimumWidth(150)

        # Bouton de création
        create_btn = QPushButton("➕ Créer une Classe")
        create_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(238,116,2,255);
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: rgba(238,116,2,200);
            }}
            QPushButton:pressed {{
                background-color: rgba(238,116,2,150);
            }}
        """)
        create_btn.clicked.connect(self.create_class)

        form_layout.addWidget(QLabel("Nom de la classe:"))
        form_layout.addWidget(self.class_name_input)
        form_layout.addWidget(QLabel("Code d'accès:"))
        form_layout.addWidget(self.class_code_input)
        form_layout.addWidget(create_btn)
        form_layout.addStretch()

        layout.addWidget(form_card)

        # Tableau des classes
        self.class_table = QTableWidget()
        self.class_table.setObjectName("classTable")
        self.class_table.setColumnCount(3)
        self.class_table.setHorizontalHeaderLabels(["Nom de la Classe", "Code d'Accès", "Étudiants"])
        self.class_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.class_table.verticalHeader().setVisible(False)
        self.class_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.class_table.setAlternatingRowColors(True)
        self.class_table.setStyleSheet(f"""
            #classTable {{
                background-color: white;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
                gridline-color: #e0e0e0;
            }}
            #classTable QHeaderView::section {{
                background-color: rgba(72,171,214,255);
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
            #classTable::item {{
                padding: 8px;
            }}
        """)
        
        # Cadre du tableau
        table_frame = QFrame()
        table_frame.setFrameShape(QFrame.StyledPanel)
        table_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
            }
        """)
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_frame.setLayout(table_layout)
        table_layout.addWidget(self.class_table)
        
        layout.addWidget(table_frame)

    def init_student_tab(self):
        """Onglet de gestion des étudiants"""
        self.student_tab = QWidget()
        self.tabs.addTab(self.student_tab, "👥 Étudiants")

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        self.student_tab.setLayout(layout)

        # Titre de section
        section_title = QLabel("👨‍🎓 Gestion des Étudiants")
        section_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        section_title.setStyleSheet("color: rgba(0,84,123,255); margin-bottom: 10px;")
        layout.addWidget(section_title)

        # Filtres
        filter_card = QWidget()
        filter_card.setObjectName("filterCard")
        filter_card.setStyleSheet("""
            #filterCard {
                background-color: white;
                border-radius: 6px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(15)
        filter_card.setLayout(filter_layout)

        # Champs de filtre
        self.class_filter = QLineEdit()
        self.class_filter.setPlaceholderText("Filtrer par classe...")
        self.class_filter.textChanged.connect(self.load_students_data)

        self.name_filter = QLineEdit()
        self.name_filter.setPlaceholderText("Filtrer par nom...")
        self.name_filter.textChanged.connect(self.load_students_data)

        # Bouton de rafraîchissement
        refresh_btn = QPushButton("🔄 Rafraîchir")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(72,171,214,255);
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: rgba(72,171,214,200);
            }}
            QPushButton:pressed {{
                background-color: rgba(72,171,214,150);
            }}
        """)
        refresh_btn.clicked.connect(self.load_students_data)

        filter_layout.addWidget(QLabel("🔍 Filtres:"))
        filter_layout.addWidget(self.class_filter)
        filter_layout.addWidget(self.name_filter)
        filter_layout.addWidget(refresh_btn)
        filter_layout.addStretch()

        layout.addWidget(filter_card)

        # Tableau des étudiants
        self.student_table = QTableWidget()
        self.student_table.setObjectName("studentTable")
        self.student_table.setColumnCount(7)
        self.student_table.setHorizontalHeaderLabels([
            "🆔 ID", "👤 Nom Complet", "🏫 Classe", "🔑 Code", "💼 Domaine", "📊 Confiance", "Actions"
        ])
        self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.student_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.student_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.student_table.verticalHeader().setVisible(False)
        self.student_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.student_table.setWordWrap(True)
        self.student_table.setAlternatingRowColors(True)
        self.student_table.setStyleSheet(f"""
            #studentTable {{
                background-color: white;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
                gridline-color: #e0e0e0;
                font-size: 12px;
            }}
            #studentTable QHeaderView::section {{
                background-color: rgba(72,171,214,255);
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
            #studentTable::item {{
                padding: 6px;
            }}
        """)
        
        # Cadre du tableau
        table_frame = QFrame()
        table_frame.setFrameShape(QFrame.StyledPanel)
        table_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
            }
        """)
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_frame.setLayout(table_layout)
        table_layout.addWidget(self.student_table)
        
        layout.addWidget(table_frame)

    def init_stats_tab(self):
        """Onglet des statistiques"""
        self.stats_tab = QWidget()
        self.tabs.addTab(self.stats_tab, "📊 Statistiques")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        self.stats_tab.setLayout(layout)
        
        # Titre de section
        section_title = QLabel("📈 Statistiques d'Orientation")
        section_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        section_title.setStyleSheet("color: rgba(0,84,123,255); margin-bottom: 10px;")
        layout.addWidget(section_title)
        
        # Cartes de statistiques
        stats_container = QHBoxLayout()
        stats_container.setSpacing(15)
        layout.addLayout(stats_container)
        
        # Création des cartes
        self.total_students_card = self.create_stat_card("👥 Étudiants Totaux", "0", "rgba(72,171,214,255)")
        self.classes_card = self.create_stat_card("🏫 Classes", "0", "rgba(238,116,2,255)")
        self.domains_card = self.create_stat_card("💼 Domaines", "0", "rgba(0,84,123,255)")
        
        stats_container.addWidget(self.total_students_card)
        stats_container.addWidget(self.classes_card)
        stats_container.addWidget(self.domains_card)
        
        # --- Ajout des graphiques ---
        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Premier affichage
        self.plot_stats()

        

    def confirm_reset_data(self):
        """Confirmation avant réinitialisation"""
        reply = QMessageBox.question(
            self, 
            'Confirmer la Réinitialisation', 
            'Êtes-vous sûr de vouloir réinitialiser TOUTES les données? Cela supprimera définitivement toutes les classes et étudiants!',
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.reset_all_data()

    def reset_all_data(self):
        """Réinitialisation de toutes les données"""
        try:
            # Supprimer tous les étudiants
            self.db.cursor.execute("DELETE FROM students")
            
            # Supprimer toutes les classes
            self.db.cursor.execute("DELETE FROM classes")
            
            # Valider les changements
            self.db.conn.commit()
            
            # Recharger les données
            self.load_data()
            
            self.show_message("Succès", "Toutes les données ont été réinitialisées avec succès.", QMessageBox.Information)
        except Exception as e:
            self.show_message("Erreur", f"Échec de la réinitialisation: {str(e)}", QMessageBox.Critical)
            logging.error(f"Erreur de réinitialisation: {str(e)}")
    
    def create_stat_card(self, title, value, color):
        """Crée une carte de statistique"""
        card = QWidget()
        card.setObjectName("statCard")
        card.setStyleSheet(f"""
            #statCard {{
                background-color: white;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        card.setLayout(layout)
        
        # Titre
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 10))
        title_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(title_label)
        
        # Valeur
        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        return card

    def update_status(self, message):
        """Met à jour la barre de statut"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.status_bar.setText(f"Dernière mise à jour: {current_time} | {message}")

    def setup_auto_refresh(self):
        """Configure le rafraîchissement automatique"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_data)
        self.refresh_timer.start(300000)  # 5 minutes
        self.update_status("Rafraîchissement automatique activé (toutes les 5 minutes)")

    def load_data(self):
        """Charge toutes les données"""
        try:
            self.load_classes_data()
            self.load_students_data()
            self.update_stats()
            self.update_status("Données chargées avec succès")
        except Exception as e:
            self.update_status(f"Erreur de chargement: {str(e)}")
            logging.error(f"Erreur de chargement: {str(e)}")

    def create_class(self):
        """Crée une nouvelle classe"""
        name = self.class_name_input.text().strip()
        code = self.class_code_input.text().strip()

        if not name or not code:
            self.show_message("Champs manquants", "Veuillez remplir tous les champs.", QMessageBox.Warning)
            return

        try:
            if self.db.create_class(name, code):
                self.show_message("Succès", "Classe créée avec succès!", QMessageBox.Information)
                self.class_name_input.clear()
                self.class_code_input.clear()
                self.load_classes_data()
            else:
                self.show_message("Erreur", "Échec de la création de la classe.", QMessageBox.Warning)
        except Exception as e:
            self.show_message("Erreur", f"Une erreur est survenue: {str(e)}", QMessageBox.Critical)

    def show_message(self, title, message, icon):
        """Affiche une boîte de message stylisée"""
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(icon)
        msg.setStyleSheet("""
            QMessageBox {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QMessageBox QLabel {
                font-size: 12px;
            }
            QMessageBox QPushButton {
                padding: 6px 12px;
                min-width: 80px;
                border-radius: 4px;
            }
        """)
        msg.exec_()

    def load_classes_data(self):
        """Charge les données des classes"""
        try:
            classes = self.db.get_all_classes()
            self.class_table.setRowCount(len(classes))
            
            for i, (name, code) in enumerate(classes):
                student_count = self.db.count_students_in_class(name)
                
                self.class_table.setItem(i, 0, self.create_table_item(name))
                self.class_table.setItem(i, 1, self.create_table_item(code))
                self.class_table.setItem(i, 2, self.create_table_item(str(student_count), 
                    highlight=(student_count == 0)))
        except Exception as e:
            self.update_status(f"Erreur de chargement des classes: {str(e)}")
            logging.error(f"Erreur de chargement des classes: {str(e)}")

    def load_students_data(self):
        """Charge les données des étudiants avec filtrage"""
        try:
            class_filter = self.class_filter.text().strip()
            name_filter = self.name_filter.text().strip()
            
            query = '''
                SELECT s.student_id, s.full_name, s.class, c.class_code
                FROM students s
                LEFT JOIN classes c ON s.class = c.class_name
                WHERE 1=1
            '''
            params = []
            
            if class_filter:
                query += " AND (s.class LIKE ? OR c.class_code LIKE ?)"
                params.extend([f"%{class_filter}%", f"%{class_filter}%"])
            
            if name_filter:
                query += " AND s.full_name LIKE ?"
                params.append(f"%{name_filter}%")
            
            students = self.db.cursor.execute(query, params).fetchall()
            self.populate_student_table(students)
        except Exception as e:
            self.update_status(f"Erreur de chargement des étudiants: {str(e)}")
            logging.error(f"Erreur de chargement des étudiants: {str(e)}")

    def update_stats(self):
        """Met à jour les statistiques et les graphiques"""
        try:
            # Nombre total d'étudiants
            total_students = self.db.cursor.execute("SELECT COUNT(*) FROM students").fetchone()[0]
            self.total_students_card.layout().itemAt(1).widget().setText(str(total_students))
            
            # Nombre total de classes
            total_classes = self.db.cursor.execute("SELECT COUNT(*) FROM classes").fetchone()[0]
            self.classes_card.layout().itemAt(1).widget().setText(str(total_classes))
            
            # Domaines uniques + collecte pour graphique
            domaines = []
            students = self.db.cursor.execute("SELECT student_id FROM students").fetchall()
            for (student_id,) in students:
                last_response = self.db.get_last_response(student_id)
                if last_response and "domaine" in last_response:
                    domaines.append(last_response["domaine"])
            
            unique_domains = len(set(domaines))
            self.domains_card.layout().itemAt(1).widget().setText(str(unique_domains))
            
            # Nombre total de réponses (corrigé → student_responses)
            total_responses = self.db.cursor.execute("SELECT COUNT(*) FROM student_responses").fetchone()[0]
            self.responses_card.layout().itemAt(1).widget().setText(str(total_responses))
            
            # Dernière mise à jour
            from datetime import datetime
            now = datetime.now().strftime("%H:%M:%S")
            self.last_update_card.layout().itemAt(1).widget().setText(now)
            
            # Mettre à jour le graphique avec les domaines
            self.plot_stats(domaines)
        
        except Exception as e:
            logging.error(f"Erreur de mise à jour des stats: {str(e)}")


    def create_table_item(self, text, highlight=False):
        """Crée un élément de tableau stylisé"""
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        
        if highlight:
            item.setBackground(QColor(255, 230, 230))
        
        return item

    def populate_student_table(self, students):
        """Remplit le tableau des étudiants"""
        self.student_table.setRowCount(len(students))
        
        for row_idx, (student_id, full_name, class_name, class_code) in enumerate(students):
            last_response = self.db.get_last_response(student_id)
            
            domaine = last_response.get("domaine", "Pas de réponse") if last_response else "Pas de réponse"
            
            # Gestion de la valeur de confiance avec 2 décimales
            confidence = 0
            if last_response and "confidence" in last_response:
                try:
                    confidence = float(last_response["confidence"])
                    confidence = f"{confidence:.2f}%"  # Format à 2 décimales
                except (ValueError, TypeError):
                    confidence = "0.00%"
            else:
                confidence = "0.00%"
            
            # Création des éléments avec style approprié
            self.student_table.setItem(row_idx, 0, self.create_table_item(student_id))
            self.student_table.setItem(row_idx, 1, self.create_table_item(full_name))
            self.student_table.setItem(row_idx, 2, self.create_table_item(class_name))
            self.student_table.setItem(row_idx, 3, self.create_table_item(class_code))
            
            # Style spécial pour la colonne domaine
            domain_item = self.create_table_item(domaine)
            if domaine == "Pas de réponse":
                domain_item.setForeground(QColor(150, 150, 150))
            self.student_table.setItem(row_idx, 4, domain_item)
            
            # Confiance avec code couleur
            confidence_item = self.create_table_item(confidence)
            try:
                conf_value = float(confidence.replace("%", ""))
                if conf_value > 70:
                    confidence_item.setForeground(QColor(39, 174, 96))  # Vert
                elif conf_value > 40:
                    confidence_item.setForeground(QColor(241, 196, 15))  # Jaune
                else:
                    confidence_item.setForeground(QColor(231, 76, 60))  # Rouge
            except ValueError:
                pass
            self.student_table.setItem(row_idx, 5, confidence_item)
            
            # Bouton de suppression
            delete_btn = QPushButton("Supprimer")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    padding: 5px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            delete_btn.clicked.connect(lambda _, sid=student_id: self.delete_student(sid))
            
            # Widget pour le bouton
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.addWidget(delete_btn)
            btn_layout.setAlignment(Qt.AlignCenter)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            
            self.student_table.setCellWidget(row_idx, 6, btn_widget)

    def delete_student(self, student_id):
        """Supprime un étudiant"""
        try:
            # Confirmation
            reply = QMessageBox.question(
                self,
                'Confirmer la Suppression',
                f'Êtes-vous sûr de vouloir supprimer l\'étudiant {student_id}?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Suppression
                self.db.cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
                self.db.conn.commit()
                
                # Rechargement
                self.load_students_data()
                self.update_stats()
                
                self.show_message("Succès", f"L'étudiant {student_id} a été supprimé.", QMessageBox.Information)
        except Exception as e:
            self.show_message("Erreur", f"Échec de la suppression: {str(e)}", QMessageBox.Critical)
            logging.error(f"Erreur de suppression: {str(e)}")

    def plot_stats(self):
        """Dessine les statistiques sous forme de graphique"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Exemple : Répartition par domaines
        domaines = []
        counts = []
        
        try:
            students = self.db.cursor.execute("SELECT student_id FROM students").fetchall()
            for (student_id,) in students:
                last_response = self.db.get_last_response(student_id)
                if last_response and "domaine" in last_response:
                    domaines.append(last_response["domaine"])
            
            # Compter les occurrences par domaine
            from collections import Counter
            counter = Counter(domaines)
            counts = list(counter.values())
            labels = list(counter.keys())
            
            if counts:
                ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=140)
                ax.set_title("Répartition des Domaines", fontsize=12)
            else:
                ax.text(0.5, 0.5, "Aucune donnée disponible", ha='center', va='center')
        
        except Exception as e:
            ax.text(0.5, 0.5, f"Erreur: {str(e)}", ha='center', va='center')
        
        self.canvas.draw()

    def closeEvent(self, event):
        """Arrête le timer à la fermeture"""
        self.refresh_timer.stop()
        event.accept()