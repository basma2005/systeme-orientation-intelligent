from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont

def create_school_card(school_info, color):
    """Create a school information card"""
    card = QWidget()
    card.setStyleSheet(f"""
        background-color: {color};
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
    """)
    
    layout = QVBoxLayout(card)
    layout.setSpacing(4)
    
    name = QLabel(f"<b>{school_info['name']}</b> • {school_info['city']}")
    name.setFont(QFont("Arial", 12, QFont.Bold))
    layout.addWidget(name)
    
    if 'domain' in school_info:
        domain = QLabel(f"📌 <b>Domaine:</b> {school_info['domain']}")
        layout.addWidget(domain)
    
    if 'duration' in school_info:
        duration = QLabel(f"⏳ <b>Durée:</b> {school_info['duration']}")
        layout.addWidget(duration)
    
    return card

def show_error_message(parent, title, message):
    """Show an error message dialog"""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec_()