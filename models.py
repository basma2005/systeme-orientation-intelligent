import os
import joblib
import logging
import numpy as np
import pandas as pd
import sys
from PyQt5.QtWidgets import QMessageBox

# Set up logging to file to capture errors
logging.basicConfig(
    filename='model_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

try:
    from tensorflow.keras.models import load_model
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logging.warning("TensorFlow not available")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class ModelLoader:
    def __init__(self):
        self.use_tensorflow = False
        self.use_demo_mode = False
        self.model = None
        self.label_encoder = None
        self.feature_columns = []
        
        # Initialize the method properly
        self.load_models = self._load_models  # Assign the method to the instance
        self.load_models()  # Now this will work
    
    def _load_models(self):
        """Load the ML models and preprocessing artifacts."""
        try:
            # Use resource_path to get the correct path for models
            model_paths = {
                'model': resource_path("ressources/models/orientation_deep_model.h5"),
                'encoder': resource_path("ressources/models/nn_label_encoder.pkl"),
                'features': resource_path("ressources/models/nn_feature_columns.pkl")
            }

            # Check if files exist
            missing_files = [name for name, path in model_paths.items() if not os.path.exists(path)]

            if missing_files:
                error_msg = f"Missing model files: {', '.join(missing_files)}"
                logging.error(error_msg)
                raise FileNotFoundError(error_msg)

            if TENSORFLOW_AVAILABLE:
                logging.info("Loading TensorFlow model...")
                try:
                    # Add TensorFlow compatibility settings
                    import tensorflow as tf
                    tf.get_logger().setLevel('ERROR')
                    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
                    
                    self.model = load_model(model_paths['model'], compile=False)
                    self.use_tensorflow = True
                    logging.info("TensorFlow model loaded successfully")
                except Exception as e:
                    logging.error(f"Error loading TensorFlow model: {str(e)}")
                    # Try to fall back to a different approach if available
                    raise

            # Load other models
            self.label_encoder = joblib.load(model_paths['encoder'])
            self.feature_columns = joblib.load(model_paths['features'])
            logging.info("All model files loaded successfully.")

        except Exception as e:
            logging.critical(f"Failed to load models: {str(e)}")
            self.use_demo_mode = True
            # Don't show message box during initialization to avoid GUI issues
            print(f"Model loading failed: {str(e)}. Using demo mode.")

    def predict(self, data):
        """Make predictions using the loaded model."""
        if self.use_demo_mode:
            return "informatique / ingénierie", 85.0
        
        try:
            df = pd.DataFrame([data])
            X = pd.get_dummies(df)

            # Ensure we have all expected features
            missing_cols = set(self.feature_columns) - set(X.columns)
            for col in missing_cols:
                X[col] = 0
            X = X[self.feature_columns]

            if self.use_tensorflow:
                pred_proba = self.model.predict(X.values.astype(np.float32))
                pred_class = np.argmax(pred_proba, axis=1)
                domaine = self.label_encoder.inverse_transform(pred_class)[0]
                confidence = np.max(pred_proba) * 100
            else:
                # Fallback if TensorFlow model didn't load but other models did
                pred_proba = self.model.predict_proba(X)
                pred_class = self.model.predict(X)
                domaine = self.label_encoder.inverse_transform(pred_class)[0]
                confidence = np.max(pred_proba) * 100

            return domaine, confidence
        
        except Exception as e:
            logging.error(f"Prediction error: {str(e)}")
            return "informatique / ingénierie", 85.0  # Fallback to demo mode