import sqlite3
from hashlib import sha256
import os
import uuid
from typing import Optional, Tuple, List, Dict, Any
import json
from datetime import datetime, date
import logging
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class StudentDatabase:
    def __init__(self, db_path=None):
        """Initialize database connection with resource path handling"""
        if db_path is None:
            db_path = resource_path('ressources/data/students.db')
        
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        """Establish database connection with error handling"""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            self.conn = sqlite3.connect(
                self.db_path,
                timeout=10,
                check_same_thread=False  # Allows multithreaded access
            )
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.cursor = self.conn.cursor()
            self._create_tables()
            logging.info("Database connection established")
            return True
        except Exception as e:
            logging.critical(f"Database connection failed: {str(e)}")
            return False

    def _ensure_connection(self):
        """Ensure database connection is active"""
        if self.conn is None:
            return self.reconnect()
        try:
            # Test connection
            self.cursor.execute("SELECT 1")
            return True
        except sqlite3.Error:
            return self.reconnect()

    def reconnect(self):
        """Reconnect to the database"""
        try:
            if self.conn:
                self.conn.close()
            return self.connect()
        except Exception as e:
            logging.error(f"Reconnection failed: {str(e)}")
            return False

    def _create_tables(self):
        """Create database schema with all required tables and indexes"""
        schema = [
            # Students table
            '''CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                class TEXT NOT NULL,
                registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME)''',
            
            # Student responses table
            '''CREATE TABLE IF NOT EXISTS student_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                response_data TEXT NOT NULL,
                submission_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                synced INTEGER DEFAULT 0,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE)''',
            
            # Classes table
            '''CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name TEXT UNIQUE NOT NULL,
                class_code TEXT UNIQUE NOT NULL,
                creation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                advisor_notes TEXT)''',
            
            # Login attempts tracking
            '''CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                attempt_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                success INTEGER,
                ip_address TEXT,
                FOREIGN KEY (student_id) REFERENCES students(student_id))''',
            
            # Administrators table
            '''CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                last_login DATETIME,
                is_superadmin INTEGER DEFAULT 0)'''
        ]

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_student_id ON students(student_id)",
            "CREATE INDEX IF NOT EXISTS idx_student_class ON students(class)",
            "CREATE INDEX IF NOT EXISTS idx_response_student ON student_responses(student_id)",
            "CREATE INDEX IF NOT EXISTS idx_class_name ON classes(class_name)",
            "CREATE INDEX IF NOT EXISTS idx_class_code ON classes(class_code)"
        ]

        try:
            # Execute all schema creation statements
            for statement in schema + indexes:
                self.cursor.execute(statement)
            self.conn.commit()
            
            # Create default admin if none exists
            self._create_default_admin()
            
        except sqlite3.Error as e:
            logging.error(f"Database initialization failed: {str(e)}")
            raise

    def _create_default_admin(self):
        """Create default admin account if no admins exist"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM admins")
            if self.cursor.fetchone()[0] == 0:
                password_hash = self._hash_password("admin123")
                self.cursor.execute('''
                    INSERT INTO admins 
                    (username, password_hash, full_name, is_superadmin)
                    VALUES (?, ?, ?, 1)
                ''', ("admin", password_hash, "Administrateur Principal"))
                self.conn.commit()
                logging.info("Default admin account created")
        except Exception as e:
            logging.error(f"Failed to create default admin: {str(e)}")

    # ========== STUDENT MANAGEMENT ==========
    def register_student(self, student_id: str, password: str, full_name: str, class_code: str) -> bool:
        """Register a new student with password"""
        if not self._ensure_connection():
            return False
            
        try:
            class_name = self.get_class_name(class_code)
            if not class_name:
                logging.error(f"Invalid class code: {class_code}")
                return False

            password_hash = self._hash_password(password)
            self.cursor.execute('''
                INSERT INTO students (student_id, password_hash, full_name, class)
                VALUES (?, ?, ?, ?)
            ''', (student_id.strip(), password_hash, full_name.strip(), class_name))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            logging.warning(f"Student ID already exists: {student_id}")
            return False
        except Exception as e:
            logging.error(f"Error registering student: {str(e)}")
            return False

    def verify_student_login(self, student_id: str, password: str, ip_address: str = None) -> bool:
        """Verify student credentials and log attempt"""
        if not self._ensure_connection():
            return False
            
        try:
            self.cursor.execute('''
                SELECT password_hash FROM students WHERE student_id = ?
            ''', (student_id,))
            result = self.cursor.fetchone()
            
            success = False
            if result and self._check_password(password, result[0]):
                success = True
                self._update_last_login(student_id, 'students')
            
            # Log the attempt
            self._log_login_attempt(student_id, success, ip_address)
            return success
            
        except Exception as e:
            logging.error(f"Login verification failed: {str(e)}")
            return False

    def get_student_info(self, student_id: str) -> Optional[Tuple[str, str]]:
        """Get student name and class only"""
        if not self._ensure_connection():
            return None
            
        try:
            self.cursor.execute('''
                SELECT full_name, class FROM students WHERE student_id = ?
            ''', (student_id,))
            return self.cursor.fetchone()
        except Exception as e:
            logging.error(f"Error fetching student info: {str(e)}")
            return None
        
    # ========== RESPONSE MANAGEMENT ==========
    def save_student_responses(self, student_id: str, responses: Dict[str, Any]) -> bool:
        """Save student orientation responses with better error handling"""
        if not self._ensure_connection():
            logging.error("Database connection failed")
            return False

        try:
            # Verify student exists
            if not self.get_student_info(student_id):
                logging.error(f"Attempt to save for non-existent student: {student_id}")
                return False

            # Safe JSON serialization
            response_json = self._safe_json_dump(responses)
            if response_json == "{}":
                logging.error("Failed to serialize responses to JSON")
                return False

            # Execute with transaction
            with self.conn:
                self.cursor.execute('''
                    INSERT INTO student_responses (student_id, response_data)
                    VALUES (?, ?)
                ''', (student_id, response_json))
            
            logging.info(f"Successfully saved responses for student: {student_id}")
            return True
            
        except sqlite3.IntegrityError as e:
            logging.error(f"Database integrity error: {str(e)}")
            return False
        except sqlite3.OperationalError as e:
            logging.error(f"Database operational error: {str(e)}")
            # Try to reconnect
            if self.reconnect():
                return self.save_student_responses(student_id, responses)
            return False
        except Exception as e:
            logging.error(f"Unexpected error saving responses: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def get_last_response(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent response for a student"""
        if not self._ensure_connection():
            return None
            
        try:
            self.cursor.execute('''
                SELECT response_data FROM student_responses 
                WHERE student_id = ?
                ORDER BY submission_date DESC 
                LIMIT 1
            ''', (student_id,))
            result = self.cursor.fetchone()
            return json.loads(result[0]) if result else None
        except Exception as e:
            logging.error(f"Error fetching last response: {str(e)}")
            return None

    # ========== CLASS MANAGEMENT ==========
    def create_class(self, class_name: str, class_code: str) -> bool:
        """Create a new class"""
        if not self._ensure_connection():
            return False
            
        try:
            self.cursor.execute('''
                INSERT INTO classes (class_name, class_code)
                VALUES (?, ?)
            ''', (class_name.strip(), class_code.strip()))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            logging.error(f"Class creation failed: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Error creating class: {str(e)}")
            return False

    def get_class_name(self, class_code: str) -> Optional[str]:
        """Get class name by its code"""
        if not self._ensure_connection():
            return None
            
        try:
            self.cursor.execute('''
                SELECT class_name FROM classes WHERE class_code = ?
            ''', (class_code.strip(),))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logging.error(f"Error fetching class name: {str(e)}")
            return None
        
    def get_admin_info(self, username: str) -> Optional[Tuple[str, str]]:
        """Get admin username and full name"""
        if not self._ensure_connection():
            return None
            
        try:
            self.cursor.execute('''
                SELECT username, full_name FROM admins WHERE username = ?
            ''', (username,))
            return self.cursor.fetchone()
        except Exception as e:
            logging.error(f"Error fetching admin info: {str(e)}")
            return None

    # ========== ADMIN MANAGEMENT ==========
    def verify_admin_login(self, username: str, password: str) -> bool:
        """Verify administrator credentials against database"""
        if not self._ensure_connection():
            return False
            
        try:
            self.cursor.execute('''
                SELECT password_hash FROM admins WHERE username = ?
            ''', (username,))
            result = self.cursor.fetchone()
            return result and self._check_password(password, result[0])
        except Exception as e:
            logging.error(f"Admin login verification failed: {str(e)}")
            return False

    # ========== UTILITY METHODS ==========
    def _hash_password(self, password: str) -> str:
        """Generate SHA-256 password hash"""
        return sha256(password.encode('utf-8')).hexdigest()

    def _check_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        return self._hash_password(password) == stored_hash

    def _update_last_login(self, identifier: str, table: str) -> None:
        """Update last login timestamp"""
        if not self._ensure_connection():
            return
            
        try:
            self.cursor.execute(f'''
                UPDATE {table} SET last_login = CURRENT_TIMESTAMP 
                WHERE {'student_id' if table == 'students' else 'username'} = ?
            ''', (identifier,))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Error updating last login: {str(e)}")

    def _log_login_attempt(self, student_id: str, success: bool, ip_address: str = None) -> None:
        """Record login attempt"""
        if not self._ensure_connection():
            return
            
        try:
            self.cursor.execute('''
                INSERT INTO login_attempts (student_id, success, ip_address)
                VALUES (?, ?, ?)
            ''', (student_id, int(success), ip_address))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Error logging login attempt: {str(e)}")

    def _safe_json_dump(self, data: Dict[str, Any]) -> str:
        """Safe JSON serialization with error handling"""
        try:
            # Handle None case
            if data is None:
                return "{}"
            
            # Handle non-serializable objects
            def default_serializer(obj):
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                elif hasattr(obj, '__dict__'):
                    return obj.__dict__
                else:
                    return str(obj)
            
            return json.dumps(data, ensure_ascii=False, default=default_serializer)
        except (TypeError, ValueError) as e:
            logging.error(f"JSON serialization error: {str(e)} - Data: {str(data)}")
            return "{}"

    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database"""
        if not self._ensure_connection():
            return False
            
        try:
            backup_conn = sqlite3.connect(backup_path)
            with backup_conn:
                self.conn.backup(backup_conn)
            backup_conn.close()
            return True
        except Exception as e:
            logging.error(f"Database backup failed: {str(e)}")
            return False

    def verify_or_create_student_by_name_and_class(self, full_name: str, class_code: str) -> Optional[str]:
        """Verify or create a student by name and class code"""
        if not self._ensure_connection():
            return None
            
        try:
            # Verify the class exists
            class_name = self.get_class_name(class_code)
            if not class_name:
                logging.error(f"Invalid class code: {class_code}")
                return None

            # Check if student already exists
            self.cursor.execute('''
                SELECT student_id FROM students 
                WHERE full_name = ? AND class = ?
            ''', (full_name.strip(), class_name))
            result = self.cursor.fetchone()

            if result:
                return result[0]  # Return existing student ID

            # Create new student if not found
            new_student_id = f"etu_{uuid.uuid4().hex[:6]}"
            default_password_hash = self._hash_password("")  # Empty password by default

            self.cursor.execute('''
                INSERT INTO students (student_id, password_hash, full_name, class)
                VALUES (?, ?, ?, ?)
            ''', (new_student_id, default_password_hash, full_name.strip(), class_name))
            self.conn.commit()
        
            logging.info(f"Created new student: {new_student_id}")
            return new_student_id

        except sqlite3.IntegrityError:
            logging.error(f"Student already exists: {full_name} in {class_name}")
            return None
        except Exception as e:
            logging.error(f"Error in verify_or_create_student: {str(e)}")
            return None

    def get_all_classes(self) -> List[Tuple[str, str]]:
        """Get all classes with their codes"""
        if not self._ensure_connection():
            return []
            
        try:
            self.cursor.execute('''
                SELECT class_name, class_code FROM classes ORDER BY class_name
            ''')
            return self.cursor.fetchall()
        except Exception as e:
            logging.error(f"Error fetching classes: {str(e)}")
            return []
        
    def count_students_in_class(self, class_name: str) -> int:
        """Count number of students in a class"""
        if not self._ensure_connection():
            return 0
            
        try:
            self.cursor.execute('''
                SELECT COUNT(*) FROM students WHERE class = ?
            ''', (class_name,))
            return self.cursor.fetchone()[0]
        except Exception as e:
            logging.error(f"Error counting students: {str(e)}")
            return 0
    
    def __del__(self):
        """Clean up database connection"""
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
        except Exception as e:
            logging.error(f"Error closing database: {str(e)}")