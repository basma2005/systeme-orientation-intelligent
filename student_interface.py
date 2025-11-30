from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QLabel, QPushButton, 
    QRadioButton, QButtonGroup, QCheckBox, QLineEdit, QTextEdit,
    QScrollArea, QGroupBox, QMessageBox
)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QDesktopServices
from PyQt5.QtCore import Qt, QUrl
from models import ModelLoader
from questions import QUESTIONS
from domain_info import DOMAIN_INFO
import logging
import pandas as pd
import numpy as np
import os
import requests
from datetime import datetime
from PyQt5.QtCore import pyqtSignal
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class StudentInterface(QWidget):
    logout_requested = pyqtSignal()
    
    def __init__(self, student_id, full_name, class_name, db):
        super().__init__()
        self.student_id = student_id
        self.full_name = full_name
        self.class_name = class_name
        self.db = db

        
        self.setWindowTitle(f"Orient'Pro - Étudiant: {full_name}")
        self.setWindowIcon(QIcon(resource_path("ressources/images/icon.png")))
        self.resize(900, 700)
        
        self.model_loader = ModelLoader()
        self.questions = QUESTIONS
        self.answers = {}
        self.use_demo_mode = False
        
        self.init_ui()
        self.check_previous_response()
    
    def init_ui(self):
        self.stack = QStackedWidget()
        self.create_welcome_page()
        self.create_questionnaire_page()
        self.create_result_page()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
        self.setLayout(layout)
        
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', Arial, sans-serif; }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)
    
    def check_previous_response(self):
        """Vérifie si l'étudiant a déjà une réponse enregistrée"""
        last_response = self.db.get_last_response(self.student_id)
        if last_response:
            self.show_results(
                last_response.get("domaine", "Inconnu"),
                last_response.get("confidence", 0)
            )
            self.stack.setCurrentIndex(2)

    def create_welcome_page(self):
        page = QWidget()
        page.setStyleSheet("background-color: rgba(247,246,242,255);")
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Header with student info
        header = QWidget()
        header.setStyleSheet("""
            background-color: rgba(0,84,122,255);
            border-radius: 10px;
            padding: 20px;
        """)
        header_layout = QVBoxLayout(header)
        
        welcome_label = QLabel("Bienvenue sur Orient'Pro")
        welcome_label.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        header_layout.addWidget(welcome_label)
        
        student_info = QLabel(f"""
            <p style='color:white; font-size:16px; margin-bottom:5px;'><b>{self.full_name}</b></p>
            <p style='color:rgba(255,255,255,0.9); font-size:14px;'>Classe: {self.class_name}</p>
            <p style='color:rgba(255,255,255,0.9); font-size:14px;'>ID: {self.student_id}</p>
        """)
        header_layout.addWidget(student_info)
        layout.addWidget(header)

        # Main content card
        content_card = QWidget()
        content_card.setStyleSheet("""
            background-color: rgba(248,247,243,255);
            border-radius: 16px;
            padding: 30px;
            border: 1px solid rgba(0,0,0,0.1);
        """)
        
        card_layout = QHBoxLayout(content_card)
        card_layout.setSpacing(40)
        card_layout.setContentsMargins(20, 20, 20, 20)

        # App icon section
        icon_container = QWidget()
        icon_container.setFixedWidth(200)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setAlignment(Qt.AlignCenter)
        
        try:
            icon_label = QLabel()
            pixmap = QPixmap(resource_path("ressources/images/icon.png")).scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_layout.addWidget(icon_label)
        except:
            icon_label = QLabel("🎯")
            icon_label.setStyleSheet("font-size: 100px;")
            icon_label.setAlignment(Qt.AlignCenter)
            icon_layout.addWidget(icon_label)
        
        card_layout.addWidget(icon_container)

        # Text content section
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setSpacing(20)

        # Title
        title_label = QLabel("Questionnaire d'Orientation Professionnelle")
        title_label.setStyleSheet("""
            color: rgba(0,84,122,255);
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        text_layout.addWidget(title_label)

        # Description
        desc = QLabel("""
            <p style='color:#555555; font-size:15px; line-height:1.6; margin-right: 20px;'>
            <b style='color:rgba(0,84,122,255);'>Orient'Pro</b> est votre assistant intelligent pour découvrir votre voie professionnelle idéale.<br><br>
            
            • <b>Évaluation complète</b> de vos compétences, intérêts et personnalité<br>
            • <b>Analyse personnalisée</b> basée sur des modèles scientifiques<br>
            • <b>Suggestions ciblées</b> de domaines et métiers correspondants<br>
            • <b>Recommandations</b> d'écoles et formations adaptées<br><br>
            
            <i>Ce questionnaire prend environ 15-20 minutes. Répondez avec sincérité pour obtenir<br>
            les résultats les plus pertinents pour votre avenir professionnel.</i>
            </p>
        """)
        text_layout.addWidget(desc)

        # Button container for both start and logout buttons
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setSpacing(20)  # Space between buttons
        
        # Start questionnaire button
        start_btn = QPushButton("Commencer le questionnaire")
        start_btn.setCursor(Qt.PointingHandCursor)
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(237,117,4,255);
                color: white;
                border-radius: 8px;
                padding: 14px 28px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                min-width: 250px;
            }
            QPushButton:hover {
                background-color: rgba(207,97,4,255);
            }
            QPushButton:pressed {
                background-color: rgba(177,77,4,255);
            }
        """)
        start_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        
        # Logout button - now placed next to start button
        logout_btn = QPushButton("Déconnexion")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0,84,122,255);
                color: white;
                border-radius: 8px;
                padding: 14px 28px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: rgba(0,64,92,255);
            }
            QPushButton:pressed {
                background-color: rgba(0,44,62,255);
            }
        """)
        logout_btn.clicked.connect(self.request_logout)
        
        # Add buttons to layout with stretch for centering
        btn_layout.addStretch()
        btn_layout.addWidget(start_btn)
        btn_layout.addWidget(logout_btn)
        btn_layout.addStretch()
        
        text_layout.addWidget(btn_container)

        card_layout.addWidget(text_container, stretch=1)
        layout.addWidget(content_card)
        layout.addStretch()
        page.setLayout(layout)
        self.stack.addWidget(page)

    def request_logout(self):
        """Handle logout request"""
        self.logout_requested.emit()
        self.close()

    def create_questionnaire_page(self):
        page = QWidget()
        page.setStyleSheet("""
            background-color: white;
            font-family: 'Segoe UI', Arial, sans-serif;
        """)

        # Main layout
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(0)

        # Floating card container
        container = QWidget()
        container.setStyleSheet("""
            background: white;
            border-radius: 12px;
            padding: 0px;
            border: 1px solid rgba(0,82,119,0.2);
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Header with progress
        header = QWidget()
        header.setStyleSheet("""
            background: rgba(0,82,119,255);
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            padding: 20px;
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(25, 15, 25, 15)

        title = QLabel("Questionnaire d'Orientation")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)

        # Progress label
        self.progress_label = QLabel("0% Complete")
        self.progress_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.progress_label.setStyleSheet("""
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 5px 12px;
            border-radius: 14px;
        """)
        header_layout.addWidget(self.progress_label, 0, Qt.AlignRight)
        container_layout.addWidget(header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: white; }
            QScrollBar:vertical { 
                background: rgba(0,82,119,0.1);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0,82,119,0.3);
                border-radius: 5px;
                min-height: 20px;
            }
        """)

        content = QWidget()
        content.setStyleSheet("background: white;")
        scroll.setWidget(content)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(25)

        # Introductory text
        intro = QLabel("""
            <p style='color:rgba(0,82,119,255); font-size:14px; line-height:1.6;'>
            This questionnaire helps us understand your skills and interests. 
            <span style='font-weight:600;'>Answer honestly</span> 
            for the most accurate results.
            </p>
        """)
        content_layout.addWidget(intro)

        # Questions container
        questions_container = QWidget()
        questions_container.setStyleSheet("""
            background: white;
            border-radius: 10px;
            padding: 5px;
        """)
        questions_layout = QVBoxLayout(questions_container)
        questions_layout.setContentsMargins(15, 15, 15, 15)
        questions_layout.setSpacing(20)

        # Track answered questions
        self.answered_questions = set()
        
        # Create question widgets
        for q_id, q_data in self.questions.items():
            question_card = QWidget()
            question_card.setStyleSheet("""
                background: white;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid rgba(0,82,119,0.1);
            """)
            card_layout = QVBoxLayout(question_card)
            card_layout.setContentsMargins(10, 10, 10, 10)
            card_layout.setSpacing(12)

            # Question text (en bleu foncé)
            question_label = QLabel(q_data["text"])
            question_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
            question_label.setStyleSheet("color: rgba(0,82,119,255);")
            card_layout.addWidget(question_label)

            # Answer widgets avec texte en noir
            if q_data["type"] == "radio":
                btn_group = QButtonGroup()
                for option in q_data["options"]:
                    radio = QRadioButton(option)
                    radio.setStyleSheet("""
                        QRadioButton {
                            font-size: 14px;
                            color: black;
                            spacing: 10px;
                            padding: 5px 0;
                        }
                        QRadioButton::indicator {
                            width: 18px;
                            height: 18px;
                            border-radius: 9px;
                            border: 2px solid rgba(0,82,119,0.5);
                        }
                        QRadioButton::indicator:checked {
                            background-color: rgba(74,172,215,255);
                            border: 2px solid rgba(74,172,215,255);
                        }
                    """)
                    btn_group.addButton(radio)
                    radio.toggled.connect(lambda checked, q=q_id: self.update_progress(q) if checked else None)
                    card_layout.addWidget(radio)
                self.answers[q_id] = btn_group

            elif q_data["type"] == "checkbox":
                checkboxes = []
                for option in q_data["options"]:
                    checkbox = QCheckBox(option)
                    checkbox.setStyleSheet("""
                        QCheckBox {
                            font-size: 14px;
                            color: black;
                            spacing: 10px;
                            padding: 5px 0;
                        }
                        QCheckBox::indicator {
                            width: 18px;
                            height: 18px;
                            border-radius: 4px;
                            border: 2px solid rgba(0,82,119,0.5);
                        }
                        QCheckBox::indicator:checked {
                            background-color: rgba(74,172,215,255);
                            border: 2px solid rgba(74,172,215,255);
                        }
                    """)
                    checkbox.stateChanged.connect(lambda state, q=q_id: self.update_progress(q))
                    checkboxes.append(checkbox)
                    card_layout.addWidget(checkbox)
                self.answers[q_id] = checkboxes

            elif q_data["type"] == "text":
                if q_id in ["objectifs", "vie_pro"]:
                    text_edit = QTextEdit()
                    text_edit.setStyleSheet("""
                        QTextEdit {
                            border: 1px solid rgba(0,82,119,0.3);
                            border-radius: 6px;
                            padding: 12px;
                            font-size: 14px;
                            min-height: 120px;
                            color: black;
                        }
                        QTextEdit:focus {
                            border: 2px solid rgba(74,172,215,255);
                        }
                    """)
                    text_edit.setPlaceholderText("Type your response here...")
                    text_edit.textChanged.connect(lambda q=q_id: self.update_progress(q))
                    card_layout.addWidget(text_edit)
                    self.answers[q_id] = text_edit
                else:
                    line_edit = QLineEdit()
                    line_edit.setStyleSheet("""
                        QLineEdit {
                            border: 1px solid rgba(0,82,119,0.3);
                            border-radius: 6px;
                            padding: 12px;
                            font-size: 14px;
                            color: black;
                        }
                        QLineEdit:focus {
                            border: 2px solid rgba(74,172,215,255);
                        }
                    """)
                    line_edit.setPlaceholderText("Type your answer...")
                    line_edit.textChanged.connect(lambda q=q_id: self.update_progress(q))
                    card_layout.addWidget(line_edit)
                    self.answers[q_id] = line_edit

            questions_layout.addWidget(question_card)

        content_layout.addWidget(questions_container)
        container_layout.addWidget(scroll)

        # Footer with action buttons
        footer = QWidget()
        footer.setStyleSheet("""
            background: white;
            border-bottom-left-radius: 12px;
            border-bottom-right-radius: 12px;
            border-top: 1px solid rgba(0,82,119,0.1);
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(25, 15, 25, 15)

        back_btn = QPushButton("← Retour")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background: white;
                color: rgba(0,82,119,255);
                border: 1px solid rgba(0,82,119,0.5);
                padding: 10px 15px;
                font-size: 14px;
                font-weight: 600;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(0,82,119,0.05);
                border: 1px solid rgba(0,82,119,0.8);
            }
        """)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        submit_btn = QPushButton("Valider ")
        submit_btn.setCursor(Qt.PointingHandCursor)
        submit_btn.setStyleSheet("""
            QPushButton {
                background: rgba(235,114,2,255);
                color: white;
                border: none;
                padding: 12px 28px;
                font-size: 14px;
                font-weight: 600;
                border-radius: 6px;
                min-width: 180px;
            }
            QPushButton:hover {
                background: rgba(235,114,2,0.9);
            }
            QPushButton:pressed {
                background: rgba(235,114,2,0.8);
            }
        """)
        submit_btn.clicked.connect(self.process_answers)

        footer_layout.addWidget(back_btn)
        footer_layout.addStretch()
        footer_layout.addWidget(submit_btn)
        container_layout.addWidget(footer)

        main_layout.addWidget(container)
        self.stack.addWidget(page)

    def update_progress(self, question_id):
        """Update the progress percentage when a question is answered"""
        self.answered_questions.add(question_id)
        total_questions = len(self.questions)
        answered_count = len(self.answered_questions)
        percentage = int((answered_count / total_questions) * 100)
        
        self.progress_label.setText(f"{percentage}% Complete")
        
        if percentage == 100:
            self.progress_label.setStyleSheet("""
                background: rgba(74,172,215,255);
                color: white;
                padding: 5px 12px;
                border-radius: 14px;
                font-weight: bold;
            """)
    
    def create_result_page(self):
        page = QWidget()
        self.result_layout = QVBoxLayout()
        self.result_layout.setContentsMargins(20, 20, 20, 20)
        self.result_layout.setSpacing(15)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { width: 12px; background: #f1f1f1; }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                min-height: 20px;
                border-radius: 6px;
            }
        """)
   
        content = QWidget()
        scroll.setWidget(content)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(20)

        # Header with results
        header = QWidget()
        header.setStyleSheet("""
            background-color: #3498db;
            border-radius: 10px;
            padding: 20px;
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(15, 15, 15, 15)

        self.icon_label = QLabel("🎯")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 72px; margin-bottom: 10px;")
        header_layout.addWidget(self.icon_label)

        self.result_title = QLabel()
        self.result_title.setFont(QFont("Arial", 24, QFont.Bold))
        self.result_title.setStyleSheet("color: white;")
        self.result_title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.result_title)

        self.confidence_label = QLabel()
        self.confidence_label.setFont(QFont("Arial", 14))
        self.confidence_label.setStyleSheet("color: #e0e0e0;")
        self.confidence_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.confidence_label)

        content_layout.addWidget(header)

        # Domain description
        desc_card = QWidget()
        desc_card.setStyleSheet("""
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
        """)
        desc_layout = QVBoxLayout(desc_card)
    
        self.description_label = QLabel()
        self.description_label.setFont(QFont("Arial", 12))
        self.description_label.setWordWrap(True)
        desc_layout.addWidget(self.description_label)
    
        content_layout.addWidget(desc_card)

        # Suggested careers
        careers_card = QWidget()
        careers_card.setStyleSheet("""
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
        """)
        careers_layout = QVBoxLayout(careers_card)
    
        careers_title = QLabel("Métiers suggérés:")
        careers_title.setFont(QFont("Arial", 14, QFont.Bold))
        careers_title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        careers_layout.addWidget(careers_title)

        self.careers_label = QLabel()
        self.careers_label.setFont(QFont("Arial", 12))
        self.careers_label.setWordWrap(True)
        self.careers_label.setStyleSheet("color: #34495e;")
        careers_layout.addWidget(self.careers_label)
    
        content_layout.addWidget(careers_card)

        # Recommended schools
        schools_card = QWidget()
        schools_card.setStyleSheet("""
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
        """)
        schools_layout = QVBoxLayout(schools_card)
    
        schools_title = QLabel("Écoles recommandées:")
        schools_title.setFont(QFont("Arial", 14, QFont.Bold))
        schools_title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        schools_layout.addWidget(schools_title)

        self.schools_container = QWidget()
        self.schools_container_layout = QVBoxLayout(self.schools_container)
        self.schools_container_layout.setContentsMargins(0, 0, 0, 0)
        self.schools_container_layout.setSpacing(15)
    
        schools_layout.addWidget(self.schools_container)
        content_layout.addWidget(schools_card)

        content_layout.addStretch()

        # Restart button
        restart_btn = QPushButton("Recommencer le questionnaire")
        restart_btn.setFont(QFont("Arial", 12))
        restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
                min-width: 250px;
                margin-top: 20px;
            }
            QPushButton:hover { background-color: #2471a3; }
            QPushButton:pressed { background-color: #1a4f73; }
        """)
        restart_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        content_layout.addWidget(restart_btn, alignment=Qt.AlignCenter)

        self.result_layout.addWidget(scroll)
        page.setLayout(self.result_layout)
        self.stack.addWidget(page)
    
    def process_answers(self):
        """Traite les réponses du questionnaire"""
        try:
            data = self.collect_answers()
            if data is None:  
                return

            if self.model_loader.use_demo_mode:
                self.show_demo_results()
                return

            domaine, confidence = self.analyze_answers(data)
            self.show_results(domaine, confidence)
            self.send_to_server(domaine, confidence, data)

        except Exception as e:
            logging.error(f"Erreur traitement réponses: {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue:\n{str(e)}")
            self.show_demo_results()

    def collect_answers(self):
        """Collecte et valide les réponses"""
        data = {}
        for q_id, q_data in self.questions.items():
            if q_data["type"] == "radio":
                checked_button = self.answers[q_id].checkedButton()
                if not checked_button:
                    QMessageBox.warning(self, "Attention", f"Veuillez répondre à la question: {q_data['text']}")
                    return None
                data[q_data["text"]] = checked_button.text()
            
            elif q_data["type"] == "checkbox":
                selected = [cb.text() for cb in self.answers[q_id] if cb.isChecked()]
                data[q_data["text"]] = ", ".join(selected) if selected else "Aucune"
            
            elif q_data["type"] == "text":
                widget = self.answers[q_id]
                value = widget.text() if isinstance(widget, QLineEdit) else widget.toPlainText()
                data[q_data["text"]] = value if value else "Non spécifié"
        
        return data

    def analyze_answers(self, data):
        """Analyse les réponses avec le modèle"""
        df = pd.DataFrame([data])
        X = pd.get_dummies(df)

        # Gérer les colonnes manquantes
        if not hasattr(self.model_loader, 'feature_columns'):
            raise ValueError("Modèle non initialisé correctement")
            
        missing_cols = set(self.model_loader.feature_columns) - set(X.columns)
        for col in missing_cols:
            X[col] = 0
        X = X[self.model_loader.feature_columns]

        # Prédiction
        if self.model_loader.use_tensorflow:
            pred_proba = self.model_loader.model.predict(X.values.astype(np.float32))
            pred_class = np.argmax(pred_proba, axis=1)
            domaine = self.model_loader.label_encoder.inverse_transform(pred_class)[0]
            confidence = np.max(pred_proba) * 100
        else:
            pred_proba = self.model_loader.model.predict_proba(X)
            pred_class = self.model_loader.model.predict(X)
            domaine = self.model_loader.label_encoder.inverse_transform(pred_class)[0]
            confidence = np.max(pred_proba) * 100

        return domaine, confidence

    def send_to_server(self, domaine, confidence, answers_data):
        """Envoie les résultats au serveur avec meilleure gestion d'erreur"""
        # Vérification locale avant envoi
        if not self.db.get_student_info(self.student_id):
            QMessageBox.warning(
                self,
                "Erreur enregistrement",
                "Votre compte étudiant n'est pas valide. Les résultats seront sauvegardés localement."
            )
            self.save_locally(domaine, confidence)
            return

        payload = {
            "student_id": self.student_id,
            "full_name": self.full_name,
            "class_name": self.class_name,
            "domaine": domaine,
            "confidence": confidence,
            "answers": answers_data
        }

        try:
            response = requests.post(
                "http://127.0.0.1:5000/api/submit",
                json=payload,
                timeout=5
            )
        
            # Gestion spécifique du 404
            if response.status_code == 404:
                error_data = response.json()
                QMessageBox.warning(
                    self,
                    "Erreur serveur",
                    f"Étudiant non trouvé sur le serveur:\n{error_data.get('error', '')}\n"
                    "Les résultats seront sauvegardés localement."
                )
                self.save_locally(domaine, confidence)
                return
            
            response.raise_for_status()
        
            # Sauvegarde dans la base de données locale
            success = self.db.save_student_responses(self.student_id, {
                "domaine": domaine,
                "confidence": confidence,
                "submission_date": datetime.now().isoformat(),
                "answers": answers_data
            })
            
            if not success:
                QMessageBox.warning(
                    self,
                    "Erreur sauvegarde",
                    "Erreur lors de la sauvegarde locale. Veuillez contacter l'administrateur."
                )
        
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(
                self,
                "Erreur réseau",
                f"Impossible de se connecter au serveur:\n{str(e)}\n"
                "Les résultats seront sauvegardés localement."
            )
            self.save_locally(domaine, confidence)

    def save_locally(self, domaine, confidence):
        """Sauvegarde de secours locale"""
        success = self.db.save_student_responses(self.student_id, {
            "domaine": domaine,
            "confidence": confidence,
            "submission_date": datetime.now().isoformat(),
            "local_backup": True  # Marqueur pour sauvegarde locale
        })
        
        if not success:
            QMessageBox.critical(
                self,
                "Erreur critique",
                "Impossible de sauvegarder les résultats. Veuillez réessayer ou contacter l'administrateur."
            )

    def show_results(self, domaine, confidence):
        """Affiche les résultats à l'étudiant"""
        # Nettoyer les anciennes écoles affichées
        while self.schools_container_layout.count():
            item = self.schools_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        domaine = domaine.strip()
        self.result_title.setText(f"Domaine recommandé: {domaine}")
        self.confidence_label.setText(f"Confiance du modèle: {confidence:.1f}%")

        # Récupérer les infos du domaine
        info = DOMAIN_INFO.get(domaine.lower(), DOMAIN_INFO["default"])
        self.icon_label.setText(info["icon"])
        self.description_label.setText(info["description"])
        self.careers_label.setText("\n".join([f"• {career}" for career in info["careers"]]))

        # Charger les écoles correspondantes
        self.load_schools(domaine)
        self.stack.setCurrentIndex(2)

    def load_schools(self, domaine):
        """Charge et affiche les écoles correspondant au domaine"""
        try:
            csv_path = resource_path("ressources/data/ecoles_maroc.csv")
            
            if not os.path.exists(csv_path):
                self.show_file_error("Le fichier 'ecoles_maroc.csv' n'a pas été trouvé")
                return

            df = pd.read_csv(csv_path)
            
            domain_mapping = {
                "arts / création": ["Arts"],
                "communication / marketing": ["Communication/Marketing"],
                "commerce / gestion": ["Commerce", "Gestion"],
                "droit / sciences politiques": ["Droit"],
                "informatique / ingénierie": ["Informatique", "Ingénierie", "Architecture"],
                "lettres / sciences humaines": ["Lettres/Sciences Humaines"],
                "recherche / sciences": ["Recherche/Sciences"],
                "santé / social": ["Santé/Social"],
                "technologie / technique": ["Technologie/Technique"],
                "architecture / urbanisme": ["Architecture"],
                "enseignement / éducation": ["Enseignement"],
                "environnement / développement durable": ["Environnement"]
            }
            
            mapped = domain_mapping.get(domaine.lower(), [])
            filtered = df[df["Domaine"].isin(mapped)] if mapped else df
            
            if filtered.empty:
                filtered = df  # Montrer toutes les écoles si aucun domaine correspondant

            self.display_school_cards(filtered)

        except Exception as e:
            logging.error(f"Erreur chargement écoles: {str(e)}")
            self.show_file_error(f"Erreur de chargement: {str(e)}")

    def display_school_cards(self, schools_df):
        """Affiche les cartes des écoles"""
        colors = ["#e3f2fd", "#e8f5e9", "#fff3e0", "#f3e5f5", "#e0f7fa"]
        
        for _, row in schools_df.iterrows():
            card = self.create_school_card(row, colors)
            self.schools_container_layout.addWidget(card)

    def create_school_card(self, school_data, colors):
        """Crée une carte d'école"""
        card = QWidget()
        card.setStyleSheet(f"""
            background-color: {colors[len(self.schools_container_layout) % len(colors)]};
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        # Nom et localisation
        name_layout = QHBoxLayout()
        icon = QLabel("🏫")
        name = QLabel(f"<b>{school_data['École']}</b> • {school_data['Ville']} • {school_data['Type']}")
        name.setStyleSheet("font-size: 16px; font-weight: bold; margin: 0; padding: 0;")
        name_layout.addWidget(icon)
        name_layout.addWidget(name)
        name_layout.addStretch()
        layout.addLayout(name_layout)

        # Autres informations (domaine, durée, etc.)
        if pd.notna(school_data.get('Domaine')):
            self.add_info_row(layout, "📌 Domaine:", school_data['Domaine'])
        
        if pd.notna(school_data.get('Durée_études')):
            self.add_info_row(layout, "⏳ Durée:", school_data['Durée_études'])
        
        if pd.notna(school_data.get('Admission')):
            self.add_info_row(layout, "🎯 Admission:", school_data['Admission'])
        
        if pd.notna(school_data.get('Spécialités')):
            self.add_info_row(layout, "📚 Spécialités:", school_data['Spécialités'])
        
        # Lien vers le site web
        if pd.notna(school_data.get('Lien')):
            link_btn = QPushButton("🔗 Visiter le site web")
            link_btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    color: #1565c0;
                    text-align: left;
                    padding: 2px 0;
                    margin: 1px 0;
                    font-size: 15px;
                }
                QPushButton:hover { color: #0d47a1; text-decoration: underline; }
            """)
            link_btn.setCursor(Qt.PointingHandCursor)
            link_btn.clicked.connect(lambda _, url=school_data['Lien']: QDesktopServices.openUrl(QUrl(url)))
            layout.addWidget(link_btn)
        
        return card

    def add_info_row(self, layout, icon, text):
        """Ajoute une ligne d'information à la carte"""
        row = QLabel(f"{icon} <b>{text}</b>")
        row.setStyleSheet("font-size: 15px; margin: 1px 0;")
        layout.addWidget(row)

    def show_file_error(self, message):
        """Affiche un message d'erreur pour les fichiers manquants"""
        error_card = QWidget()
        error_card.setStyleSheet("""
            background-color: #ffebee;
            border-radius: 8px;
            padding: 15px;
        """)
        error_layout = QVBoxLayout(error_card)
        
        title = QLabel("❌ Erreur")
        title.setStyleSheet("font-weight: bold; color: #c62828;")
        error_layout.addWidget(title)
        
        desc = QLabel(message)
        desc.setWordWrap(True)
        error_layout.addWidget(desc)
        
        self.schools_container_layout.addWidget(error_card)

    def show_demo_results(self):
        """Affiche des résultats de démonstration"""
        self.show_results("Informatique / Ingénierie", 85.0)