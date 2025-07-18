# database.py
import sqlite3
from . import config 

def create_reviews_table():
    """Crée la table 'reviews_nickel' si elle n'existe pas."""
    with sqlite3.connect(config.DATABASE_PATH) as conn:
        c = conn.cursor()
        c.execute(config.TABLE_SCHEMA)
        conn.commit()
    print(f"Table 'reviews_nickel' vérifiée/créée dans {config.DATABASE_PATH}.")

def insert_review_data(review_data):
    """
    Insère un avis dans la base de données.
    Vérifie l'unicité par contenu_hash avant l'insertion.
    Retourne True si l'avis a été inséré, False sinon (doublon).
    """
    with sqlite3.connect(config.DATABASE_PATH) as conn:
        c = conn.cursor()
        contenu_hash = review_data.get('contenu_hash')

        if contenu_hash: 
            c.execute("SELECT COUNT(*) FROM reviews_nickel WHERE contenu_hash = ?", (contenu_hash,))
            if c.fetchone()[0] == 0:
                c.execute("""
                    INSERT INTO reviews_nickel (nom, nombre_avis, langue_origine, note_avis, 
                           date_publication, date_experience, jour_experience, mois_experience, 
                          annee_experience, contenu_avis, contenu_hash, avis_sur_invitation, 
                           sentiment, reponse, date_reponse, date_scraping)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    review_data.get('nom'),
                    review_data.get('nombre_avis'),
                    review_data.get('langue_origine'),
                    review_data.get('note_avis'),
                    review_data.get('date_publication'),
                    review_data.get('date_experience'),
                    review_data.get('jour_experience'),
                    review_data.get('mois_experience'),
                    review_data.get('annee_experience'),
                    review_data.get('contenu_avis'),
                    review_data.get('contenu_hash'),
                    review_data.get('avis_sur_invitation'),
                    review_data.get('sentiment'),
                    review_data.get('reponse'),
                    review_data.get('date_reponse'),
                    review_data.get('date_scraping')
                ))
                conn.commit()
                return True
        return False # Retourne False si pas de hash ou si doublon