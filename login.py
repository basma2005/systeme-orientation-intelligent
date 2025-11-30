from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QWidget, QMessageBox, QComboBox
)
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtCore import Qt, pyqtSignal
from hashlib import sha256
import logging
import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class LoginDialog(QDialog):
    login_success = pyqtSignal(str, str, str)  # (user_type, identifier, full_name)

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Connexion - Orient'Pro")
        self.setWindowIcon(QIcon(resource_path("ressources/images/icon.png")))
        self.resize(900, 500)
        self.setWindowFlags(self.windowFlags() | 
                           Qt.WindowMinimizeButtonHint | 
                           Qt.WindowMaximizeButtonHint |
                           Qt.WindowCloseButtonHint)
        self.setStyleSheet("background-color: #ecf0f1;")  # gris très clair
        self._init_ui()

    def _init_ui(self):
        # Couleurs principales
        orange = "#EE7402"
        blue_dark = "#00547B"
        blue_light = "#48ABD6"
        logo_bg_color = "rgba(247, 246, 242, 255)"  
        logo_text_color = "#00547B" 

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        # Logo à gauche
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet(f"""
            background-color: {logo_bg_color};
            padding: 30px;
            border-top-left-radius: 15px;
            border-bottom-left-radius: 15px;
        """)
        self._update_logo()
        self.logo_label.setFixedWidth(320)
        main_layout.addWidget(self.logo_label)

        # Formulaire à droite
        form_container = QWidget()
        form_container.setStyleSheet("""
            background-color: white;
            border-top-right-radius: 15px;
            border-bottom-right-radius: 15px;
        """)
        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(40, 40, 40, 40)
        form_layout.setSpacing(25)
        form_container.setLayout(form_layout)

        title = QLabel("Connexion à Orient'Pro")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            color: {blue_dark};
            font-size: 24px;
            font-weight: bold;
        """)
        form_layout.addWidget(title)

        self.form_fields = QFormLayout()
        self.form_fields.setVerticalSpacing(20)
        self.form_fields.setHorizontalSpacing(15)

        # ComboBox
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Étudiant", "Administrateur"])
        self.role_combo.setMinimumHeight(40)
        self.role_combo.setStyleSheet(f"""
            QComboBox {{
                font-size: 16px;
                padding: 10px;
                border: 2px solid {blue_light};
                border-radius: 6px;
                background-color: #f2f9fc;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)
        self.form_fields.addRow(QLabel("<font size='5'>Type de compte:</font>"), self.role_combo)

        # Inputs
        input_style = f"""
            font-size: 16px;
            padding: 10px;
            border: 2px solid {blue_light};
            border-radius: 6px;
            background-color: #fdfdfd;
        """

        self.name_input = QLineEdit()
        self.name_input.setMinimumHeight(40)
        self.name_input.setStyleSheet(input_style)

        self.class_code_input = QLineEdit()
        self.class_code_input.setPlaceholderText("Code classe")
        self.class_code_input.setMinimumHeight(40)
        self.class_code_input.setStyleSheet(input_style)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.setStyleSheet(input_style)

        # Labels
        self.name_label = QLabel("<font size='5'>Nom complet:</font>")
        self.class_code_label = QLabel("<font size='5'>Code classe:</font>")
        self.password_label = QLabel("<font size='5'>Mot de passe:</font>")

        self.form_fields.addRow(self.name_label, self.name_input)
        self.form_fields.addRow(self.class_code_label, self.class_code_input)
        self.form_fields.addRow(self.password_label, self.password_input)

        form_layout.addLayout(self.form_fields)

        # Bouton connexion
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(30)

        login_btn = QPushButton("Se connecter")
        login_btn.setMinimumSize(160, 45)
        login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {orange};
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 16px;
                padding: 12px 24px;
            }}
            QPushButton:hover {{
                background-color: {blue_light};
            }}
            QPushButton:pressed {{
                background-color: {blue_dark};
            }}
        """)
        login_btn.clicked.connect(self._handle_login)

        btn_layout.addWidget(login_btn)
        form_layout.addLayout(btn_layout)

        # Label erreur
        self.error_label = QLabel()
        self.error_label.setStyleSheet("""
            color: red;
            font-size: 14px;
            padding: 10px;
            background-color: #ffe6e6;
            border-radius: 6px;
        """)
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        form_layout.addWidget(self.error_label)

        main_layout.addWidget(form_container, stretch=2)

        self.role_combo.currentTextChanged.connect(self._update_form_fields)
        self._update_form_fields(self.role_combo.currentText())

    def _update_form_fields(self, role):
        is_student = role == "Étudiant"
        self.name_label.setText("<font size='5'>Nom complet:</font>" if is_student else "<font size='5'>Identifiant:</font>")
        self.class_code_label.setVisible(is_student)
        self.class_code_input.setVisible(is_student)
        self.password_label.setVisible(not is_student)
        self.password_input.setVisible(not is_student)
        self.name_input.setPlaceholderText("Entrez votre nom complet" if is_student else "Entrez votre identifiant")
        self.error_label.clear()

    def _handle_login(self):
        try:
            role = self.role_combo.currentText()
            name = self.name_input.text().strip()

            if role == "Étudiant":
                class_code = self.class_code_input.text().strip()
                if not name or not class_code:
                    self.error_label.setText("Veuillez remplir le nom complet et le code classe.")
                    return

                student_id = self.db.verify_or_create_student_by_name_and_class(name, class_code)
                if not student_id:
                    self.error_label.setText("Nom complet ou code classe incorrect.")
                    return

                student_info = self.db.get_student_info(student_id)
                if not student_info:
                    self.error_label.setText("Informations étudiant non trouvées.")
                    return

                full_name, class_name = student_info
                self.login_success.emit('student', student_id, full_name)
                self.accept()

            else:
                password = self.password_input.text().strip()
                if not name or not password:
                    self.error_label.setText("Veuillez remplir l'identifiant et le mot de passe.")
                    return

                if self.db.verify_admin_login(name, password):
                    admin_info = self.db.get_admin_info(name)
                    if admin_info:
                        username, full_name = admin_info
                        self.login_success.emit('advisor', username, full_name)
                        self.accept()
                    else:
                        self.error_label.setText("Informations administrateur non trouvées.")
                else:
                    self.error_label.setText("Identifiants administrateur incorrects.")

        except Exception as e:
            self.error_label.setText(f"Une erreur est survenue: {str(e)}")
            logging.error(f"Login error: {str(e)}")

    def _update_logo(self):
        try:
            pixmap = QPixmap(resource_path("ressources/images/logo.png"))
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.logo_label.setPixmap(scaled_pixmap)
        except Exception as e:
            logging.warning(f"Erreur de chargement du logo: {str(e)}")
            self.logo_label.setText("Orient'Pro")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_logo()