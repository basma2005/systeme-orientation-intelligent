from flask import Flask, request, jsonify
import json
import logging
from datetime import datetime
from database import StudentDatabase
from flask_cors import CORS
import time
import sqlite3

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.config.update({
    'JSONIFY_PRETTYPRINT_REGULAR': True,
    'JSON_SORT_KEYS': False,
    'SQLITE_THREADSAFE': 1,
    'SQLITE_DB_TIMEOUT': 10,
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024  # 16MB max request size
})

# Initialize database with connection pooling
db = StudentDatabase()

@app.before_request
def before_request():
    """Verify and maintain database connection before each request"""
    try:
        if not hasattr(db, 'conn') or not db.conn:
            db.connect()
        # Simple connection test
        db.cursor.execute("SELECT 1")
    except (sqlite3.Error, AttributeError) as e:
        logging.error(f"Database connection check failed: {str(e)}")
        try:
            db.connect()  # Attempt to reconnect
        except Exception as reconnect_error:
            logging.critical(f"Database reconnection failed: {str(reconnect_error)}")
            return jsonify({
                "error": "Database unavailable",
                "message": "Service temporarily unavailable"
            }), 503

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint for service health monitoring"""
    try:
        # Check database connection
        db.cursor.execute("SELECT 1")
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/api/students', methods=['GET'])
def get_students():
    """Get all students with their last response"""
    try:
        students_data = []
        
        query = '''
            SELECT s.student_id, s.full_name, s.class, 
                   c.class_code,
                   COALESCE(r.response_data, '{}') as response_data,
                   r.submission_date
            FROM students s
            LEFT JOIN classes c ON s.class = c.class_name
            LEFT JOIN (
                SELECT student_id, response_data, MAX(submission_date) as submission_date
                FROM student_responses
                GROUP BY student_id
            ) r ON s.student_id = r.student_id
            ORDER BY s.class, s.full_name
        '''
        
        with db.conn:
            db.cursor.execute(query)
            for row in db.cursor.fetchall():
                try:
                    response = json.loads(row[4]) if row[4] else {}
                except json.JSONDecodeError as je:
                    logging.warning(f"Invalid JSON for student {row[0]}: {str(je)}")
                    response = {}
                
                students_data.append({
                    "ID": row[0],
                    "Nom complet": row[1],
                    "Classe": row[2],
                    "Code": row[3] if row[3] else "N/A",
                    "Domaine": response.get("domaine", "Aucune réponse"),
                    "Confiance": f"{response.get('confidence', 0):.1f}%",
                    "Date": row[5].strftime("%Y-%m-%d %H:%M:%S") if row[5] else ""
                })

        return jsonify(students_data), 200

    except Exception as e:
        logging.error(f"Error fetching students: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "request_id": request.headers.get('X-Request-ID', 'none')
        }), 500

@app.route('/api/students/by_class/<class_name>', methods=['GET'])
def get_students_by_class(class_name):
    """Get students by class with domain info"""
    try:
        if not class_name.replace('_', ' ').replace('-', ' ').isalnum():
            return jsonify({
                "error": "Invalid class name format",
                "valid_format": "Alphanumeric with spaces, underscores or hyphens"
            }), 400

        normalized_class_name = class_name.replace('_', ' ').replace('-', ' ')
        students_data = []
        
        query = '''
            SELECT s.student_id, s.full_name, s.class,
                   COALESCE(r.response_data, '{}') as response_data,
                   r.submission_date
            FROM students s
            LEFT JOIN (
                SELECT student_id, response_data, MAX(submission_date) as submission_date
                FROM student_responses
                GROUP BY student_id
            ) r ON s.student_id = r.student_id
            WHERE s.class = ?
            ORDER BY s.full_name
        '''
        
        with db.conn:
            db.cursor.execute(query, (normalized_class_name,))
            for row in db.cursor.fetchall():
                try:
                    response = json.loads(row[3]) if row[3] else {}
                except json.JSONDecodeError:
                    response = {}

                students_data.append({
                    "ID": row[0],
                    "Nom complet": row[1],
                    "Classe": row[2],
                    "Domaine": response.get("domaine", "Aucune réponse"),
                    "Confiance": f"{response.get('confidence', 0):.1f}%",
                    "Date": row[4].strftime("%Y-%m-%d %H:%M:%S") if row[4] else ""
                })

        return jsonify(students_data), 200

    except Exception as e:
        logging.error(f"Error fetching class students: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "class": class_name
        }), 500

@app.route('/api/submit', methods=['POST'])
def submit_response():
    """Submit student orientation results with retry logic"""
    max_retries = 3
    retry_delay = 0.1  # seconds
    
    try:
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        required_fields = ["student_id", "domaine", "confidence"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            return jsonify({
                "error": "Missing required fields",
                "missing": missing_fields
            }), 400

        # Student verification
        student_info = db.get_student_info(data["student_id"])
        if not student_info:
            logging.warning(f"Unknown student: {data['student_id']}")
            return jsonify({
                "error": "Student not found",
                "student_id": data["student_id"]
            }), 404

        # Data validation
        try:
            confidence = float(data["confidence"])
            if not 0 <= confidence <= 100:
                raise ValueError("Confidence out of range")
        except ValueError as ve:
            return jsonify({
                "error": "Invalid confidence value",
                "message": str(ve),
                "received": data["confidence"]
            }), 400

        # Prepare response data
        response_data = {
            "domaine": data["domaine"],
            "confidence": confidence,
            "submission_date": datetime.now().isoformat(),
            "full_name": student_info[0],
            "class_name": student_info[1]
        }

        # Save with retry logic
        for attempt in range(max_retries):
            try:
                if db.save_student_responses(data["student_id"], response_data):
                    return jsonify({
                        "status": "success",
                        "student_id": data["student_id"],
                        "domaine": data["domaine"],
                        "confidence": confidence,
                        "timestamp": response_data["submission_date"]
                    }), 200
                break
            except sqlite3.OperationalError as oe:
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay)
                logging.warning(f"Retry {attempt + 1} for student {data['student_id']}")

        return jsonify({
            "error": "Failed to save response",
            "student_id": data["student_id"]
        }), 500

    except Exception as e:
        logging.error(f"Submission error: {str(e)}\nData: {data}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e),
            "request_id": request.headers.get('X-Request-ID', 'none')
        }), 500

@app.route('/api/classes', methods=['GET'])
def get_classes():
    """Get all classes with student counts"""
    try:
        classes_data = []
        
        query = '''
            SELECT c.class_name, c.class_code, 
                   COUNT(s.student_id) as student_count
            FROM classes c
            LEFT JOIN students s ON c.class_name = s.class
            GROUP BY c.class_name, c.class_code
            ORDER BY c.class_name
        '''
        
        with db.conn:
            db.cursor.execute(query)
            for row in db.cursor.fetchall():
                classes_data.append({
                    "class_name": row[0],
                    "class_code": row[1],
                    "student_count": row[2]
                })

        return jsonify(classes_data), 200

    except Exception as e:
        logging.error(f"Error fetching classes: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "path": request.path,
        "available_endpoints": {
            "GET /api/students": "List all students",
            "GET /api/students/by_class/<class_name>": "Get students by class",
            "GET /api/classes": "List all classes with student counts",
            "POST /api/submit": "Submit orientation results",
            "POST /api/verify_student": "Verify student exists",
            "GET /api/health": "Service health check"
        }
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal server error: {str(error)}")
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred",
        "request_id": request.headers.get('X-Request-ID', 'none')
    }), 500

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s [%(request_id)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    try:
        # Initial connection test
        db.connect()
        db.cursor.execute("SELECT 1")
        logging.info("Database connection established successfully")
    except Exception as e:
        logging.critical(f"Failed to initialize database: {str(e)}")
        raise

    app.run(host='0.0.0.0', port=5000, debug=False)