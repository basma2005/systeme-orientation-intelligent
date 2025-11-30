import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import joblib
import matplotlib.pyplot as plt

def main():
    # 1. Charger les données
    df = pd.read_csv("ressources/data/dataset_orientation.csv")
    
    # 2. Prétraitement des données
    if "Horodateur" in df.columns:
        df = df.drop(columns=["Horodateur"])
    
    target_col = "Champ convenable"
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Encodage des labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Encodage One-Hot des features
    X_encoded = pd.get_dummies(X)
    feature_columns = X_encoded.columns.tolist()
    
    # 3. Séparation train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X_encoded, y_encoded, test_size=0.2, random_state=42
    )
    
    # 4. Construction du modèle
    model = Sequential([
        Dense(256, activation='relu', input_shape=(X_train.shape[1],)),
        Dropout(0.3),
        Dense(128, activation='relu'),
        Dropout(0.2),
        Dense(len(label_encoder.classes_), activation='softmax')
    ])
    
    model.compile(
        loss='sparse_categorical_crossentropy',
        optimizer='adam',
        metrics=['accuracy']
    )
    
    # 5. Entraînement avec historique
    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    
    print("Début de l'entraînement...")
    history = model.fit(
        X_train, y_train,
        validation_split=0.2,
        epochs=100,
        batch_size=32,
        callbacks=[early_stop],
        verbose=1
    )
    
    # 6. Générer la courbe d'apprentissage
    plot_learning_curve(history)
    
    # 7. Évaluation
    y_pred = np.argmax(model.predict(X_test), axis=1)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy:.2f}")
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))
    
    # 8. Sauvegarde des modèles
    os.makedirs("ressources/models", exist_ok=True)
    os.makedirs("ressources/graphiques", exist_ok=True)
    
    model.save("ressources/models/orientation_deep_model.h5", save_format="h5")
    joblib.dump(label_encoder, "ressources/models/nn_label_encoder.pkl")
    joblib.dump(feature_columns, "ressources/models/nn_feature_columns.pkl")
    
    # Sauvegarder l'historique d'entraînement
    joblib.dump(history.history, "ressources/models/training_history.pkl")
    
    print("Modèles et courbe d'apprentissage sauvegardés avec succès!")

def plot_learning_curve(history):
    """Génère et sauvegarde la courbe d'apprentissage"""
    
    # Créer une figure avec deux sous-graphiques
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    # Courbe de précision
    ax1.plot(history.history['accuracy'], label='Accuracy Entraînement', linewidth=2)
    ax1.plot(history.history['val_accuracy'], label='Accuracy Validation', linewidth=2)
    ax1.set_title('Courbe de Précision', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Époques')
    ax1.set_ylabel('Précision')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Courbe de loss
    ax2.plot(history.history['loss'], label='Loss Entraînement', linewidth=2)
    ax2.plot(history.history['val_loss'], label='Loss Validation', linewidth=2)
    ax2.set_title('Courbe de Perte', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Époques')
    ax2.set_ylabel('Loss')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Ajuster l'espacement
    plt.tight_layout()
    
    # Sauvegarder le graphique
    plt.savefig('ressources/graphiques/courbe_apprentissage.png', 
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig('ressources/graphiques/courbe_apprentissage.pdf', 
                bbox_inches='tight', facecolor='white')
    
    # Afficher le graphique
    plt.show()
    
    # Afficher les statistiques finales
    final_train_acc = history.history['accuracy'][-1]
    final_val_acc = history.history['val_accuracy'][-1]
    final_train_loss = history.history['loss'][-1]
    final_val_loss = history.history['val_loss'][-1]
    
    print(f"\n=== STATISTIQUES FINALES D'ENTRAÎNEMENT ===")
    print(f"Précision finale - Entraînement: {final_train_acc:.4f}")
    print(f"Précision finale - Validation: {final_val_acc:.4f}")
    print(f"Loss finale - Entraînement: {final_train_loss:.4f}")
    print(f"Loss finale - Validation: {final_val_loss:.4f}")
    print(f"Nombre d'époques effectuées: {len(history.history['accuracy'])}")
    
    # Trouver la meilleure époque pour la validation
    best_epoch_val = np.argmax(history.history['val_accuracy']) + 1
    best_val_acc = np.max(history.history['val_accuracy'])
    print(f"Meilleure accuracy validation: {best_val_acc:.4f} (époque {best_epoch_val})")

def load_and_plot_existing_history():
    """Charge et affiche l'historique d'entraînement existant"""
    try:
        history = joblib.load("ressources/models/training_history.pkl")
        plot_learning_curve(type('History', (), {'history': history})())
    except FileNotFoundError:
        print("Aucun historique d'entraînement trouvé. Veuillez d'abord entraîner le modèle.")

if __name__ == "__main__":
    main()
    
    # Optionnel: Pour visualiser un historique existant
    # load_and_plot_existing_history()