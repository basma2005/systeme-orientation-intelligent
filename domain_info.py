import sys
import os
import pandas as pd

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# If you load data from CSV files
def load_schools_data():
    schools_path = resource_path('ressources/data/ecoles_maroc.csv')
    return pd.read_csv(schools_path)

def load_orientation_dataset():
    dataset_path = resource_path('ressources/data/dataset_orientation.csv')
    return pd.read_csv(dataset_path)
    
DOMAIN_INFO = {
        "informatique / ingénierie": {
            "icon": "💻",
            "description": "Votre profil montre d'excellentes aptitudes pour les technologies et la résolution de problèmes techniques. Vous seriez bien adapté aux métiers de l'informatique et de l'ingénierie.",
            "careers": [
                "Développeur Logiciel",
                "Ingénieur Système",
                "Data Scientist",
                "Ingénieur en Cybersécurité",
                "Architecte Logiciel",
                "Ingénieur Cloud",
                "Administrateur Base de Données"
            ]
        },
        "technologie / technique": {
            "icon": "⚙️",
            "description": "Votre profil technique et votre goût pour les solutions concrètes vous orientent vers les métiers de la technologie et des sciences appliquées.",
            "careers": [
                "Ingénieur Mécanique",
                "Technicien Supérieur",
                "Ingénieur Industriel",
                "Expert en Automatisation",
                "Chef de Projet Technique",
                "Ingénieur Qualité"
            ]
        },
        "arts / création": {
            "icon": "🎨",
            "description": "Votre créativité et votre sens artistique marqués vous destinent à des carrières dans les domaines artistiques et créatifs.",
            "careers": [
                "Designer Graphique",
                "Artiste Plasticien",
                "Directeur Artistique",
                "Architecte d'Intérieur",
                "Photographe",
                "Animateur 3D"
            ]
        },
        "communication / marketing": {
            "icon": "📢",
            "description": "Vos talents de communication et votre aisance relationnelle sont des atouts pour les métiers du marketing et de la communication.",
            "careers": [
                "Responsable Marketing",
                "Chargé de Communication",
                "Community Manager",
                "Chef de Publicité",
                "Responsable Événementiel",
                "Journaliste"
            ]
        },
        "lettres / sciences humaines": {
            "icon": "📚",
            "description": "Votre intérêt pour les sciences humaines et votre esprit d'analyse vous ouvrent des perspectives dans divers domaines littéraires.",
            "careers": [
                "Enseignant",
                "Chercheur en Sciences Humaines",
                "Éditeur",
                "Traducteur",
                "Conseiller en Orientation",
                "Bibliothécaire"
            ]
        },
        "recherche / sciences": {
            "icon": "🔬",
            "description": "Votre esprit scientifique et votre curiosité intellectuelle sont des atouts pour une carrière dans la recherche scientifique.",
            "careers": [
                "Chercheur en Biologie",
                "Physicien",
                "Chimiste",
                "Mathématicien",
                "Géologue",
                "Astronome"
            ]
        },
        "santé / social": {
            "icon": "🏥",
            "description": "Votre intérêt pour les autres et votre sens du service vous orientent vers les métiers de la santé et du social.",
            "careers": [
                "Médecin",
                "Infirmier",
                "Psychologue",
                "Assistant Social",
                "Éducateur Spécialisé",
                "Ergothérapeute"
            ]
        },
        "commerce / gestion": {
            "icon": "💰",
            "description": "Vos aptitudes pour la gestion et le commerce vous prédisposent à des carrières dans le monde des affaires.",
            "careers": [
                "Responsable Commercial",
                "Chef de Projet",
                "Analyste Financier",
                "Responsable RH",
                "Entrepreneur",
                "Responsable Logistique"
            ]
        },
        "droit / sciences politiques": {
            "icon": "⚖️",
            "description": "Votre sens de la justice et votre intérêt pour les questions sociétales vous orientent vers les carrières juridiques et politiques.",
            "careers": [
                "Avocat",
                "Juriste d'Entreprise",
                "Notaire",
                "Diplomate",
                "Fonctionnaire International",
                "Consultant en Droit"
            ]
        },
        "architecture / urbanisme": {
            "icon": "🏛️",
            "description": "Votre sens de l'espace et votre créativité technique vous destinent aux métiers de l'architecture et de l'urbanisme.",
            "careers": [
                "Architecte",
                "Urbaniste",
                "Designer d'Espace",
                "Architecte Paysagiste",
                "Ingénieur en BTP",
                "Conseiller en Urbanisme"
            ]
        },
        "enseignement / éducation": {
            "icon": "📝",
            "description": "Votre pédagogie et votre envie de transmettre vous orientent vers les métiers de l'enseignement et de l'éducation.",
            "careers": [
                "Professeur",
                "Formateur",
                "Conseiller Pédagogique",
                "Éducateur",
                "Directeur d'Établissement",
                "Chercheur en Éducation"
            ]
        },
        "environnement / développement durable": {
            "icon": "🌱",
            "description": "Votre sensibilité écologique et votre intérêt pour les enjeux environnementaux vous destinent aux métiers du développement durable.",
            "careers": [
                "Ingénieur Environnement",
                "Responsable QHSE",
                "Consultant en Développement Durable",
                "Écologue",
                "Chargé de Mission Environnement",
                "Géomaticien"
            ]
        },
        "default": {
            "icon": "🎯",
            "description": "Votre profil polyvalent ouvre de nombreuses possibilités professionnelles dans divers secteurs d'activité.",
            "careers": [
                "Consultant",
                "Chef de Projet",
                "Entrepreneur",
                "Manager",
                "Responsable d'Équipe",
                "Coordinateur"
            ]
        }
}