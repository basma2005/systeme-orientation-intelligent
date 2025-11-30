import sys
import os
import threading
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from database import StudentDatabase
from login import LoginDialog
from student_interface import StudentInterface
from advisor_interface import AdvisorDashboard
from server import app as flask_app

# Add global exception handler
def exception_handler(exc_type, exc_value, exc_traceback):
    """Global exception handler that writes to a file"""
    # Skip handling for keyboard interrupts
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Try to write to error log file
    try:
        with open('error.log', 'a', encoding='utf-8') as f:
            f.write(f"Error occurred: {error_msg}\n")
    except Exception as file_error:
        print(f"Could not write to error log: {file_error}")
    
    # Show error message to user
    try:
        QMessageBox.critical(
            None, 
            "Application Error", 
            f"An unexpected error occurred:\n\n{str(exc_value)}\n\nSee error.log for details."
        )
    except:
        pass  # If we can't show message box, at least don't crash

# Set the exception handler
sys.excepthook = exception_handler

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class OrientationApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        # Set up database with resource path handling
        db_path = resource_path('ressources/data/students.db')
        self.db = StudentDatabase(db_path)
        
        # Test database connection
        if not self.db._ensure_connection():
            QMessageBox.critical(None, "Erreur de Base de Données", 
                "Impossible de se connecter à la base de données.\n"
                "Vérifiez que le fichier students.db existe dans le dossier ressources/data/")
            sys.exit(1)
        
        self.current_user_id = None
        self.current_user_type = None
        self.current_user_name = None
        self.login_dialog = None
        self.interface = None
        
        # Start the server in a background thread (without opening browser)
        self.start_server()
        self.show_login()

    def start_server(self):
        """Start the Flask server in a background thread without opening browser"""
        def run_server():
            try:
                # Disable Flask development features for production
                flask_app.run(port=5000, use_reloader=False, debug=False, threaded=True)
            except Exception as e:
                # Write error to log but don't crash the application
                try:
                    with open('server_error.log', 'a', encoding='utf-8') as f:
                        f.write(f"Server error: {e}\n")
                except:
                    pass
                
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        print("Flask server started on port 5000 (browser not automatically opened)")

    def show_login(self):
        """Show the login dialog and clean up any existing interface"""
        # Reset current user information
        self.current_user_id = None
        self.current_user_type = None
        self.current_user_name = None
        
        # Close any existing interface
        if self.interface:
            try:
                self.interface.close()
            except:
                pass
            self.interface = None
            
        # Create and show new login dialog
        try:
            self.login_dialog = LoginDialog(self.db)
            self.login_dialog.login_success.connect(self.on_login_success)
            self.login_dialog.show()
        except Exception as e:
            QMessageBox.critical(None, "Login Error", f"Failed to create login dialog: {str(e)}")
            sys.exit(1)

    def on_login_success(self, user_type, user_id, user_name):
        """Handle successful login and launch appropriate interface"""
        try:
            self.current_user_type = user_type
            self.current_user_id = user_id
            self.current_user_name = user_name
            
            # Close login dialog
            if self.login_dialog:
                self.login_dialog.close()
                self.login_dialog = None

            if user_type == 'student':
                self.launch_student_interface(user_id)
            elif user_type == 'advisor':
                self.launch_advisor_interface()
            else:
                QMessageBox.critical(None, "Error", "Unknown user type")
                self.show_login()

        except Exception as e:
            QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}")
            self.show_login()

    def launch_student_interface(self, user_id):
        """Launch the student interface"""
        try:
            student_info = self.db.get_student_info(user_id)
            if not student_info:
                QMessageBox.critical(None, "Error", "Student information not found")
                self.show_login()
                return

            full_name, class_name = student_info
            self.interface = StudentInterface(
                student_id=user_id,
                full_name=full_name,
                class_name=class_name,
                db=self.db
            )
            
            if hasattr(self.interface, 'logout_requested'):
                self.interface.logout_requested.connect(self.show_login)
                
            self.interface.show()
            
        except Exception as e:
            QMessageBox.critical(None, "Interface Error", f"Failed to launch student interface: {str(e)}")
            self.show_login()

    def launch_advisor_interface(self):
        """Launch the advisor interface"""
        try:
            self.interface = AdvisorDashboard(self.db)
            
            if hasattr(self.interface, 'logout_requested'):
                self.interface.logout_requested.connect(self.show_login)
            elif hasattr(self.interface, 'return_to_login_signal'):
                self.interface.return_to_login_signal.connect(self.show_login)
                
            self.interface.show()
            
        except Exception as e:
            QMessageBox.critical(None, "Interface Error", f"Failed to launch advisor interface: {str(e)}")
            self.show_login()

    def run(self):
        """Run the application"""
        try:
            sys.exit(self.app.exec_())
        except Exception as e:
            QMessageBox.critical(None, "Runtime Error", f"Application runtime error: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    try:
        # Set up application-wide styles
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        
        # Create and run main application
        orientation_app = OrientationApp()
        orientation_app.run()
        
    except Exception as e:
        QMessageBox.critical(None, "Fatal Error", f"Application failed to start: {str(e)}")
        sys.exit(1)