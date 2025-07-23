# database.py
from . import config
from datetime import datetime, date 

#########################################################
################### postgresql ###################
import psycopg2 # Pour PostgreSQL
from . import config 
import logging # Pour des logs d'erreurs plus robustes
# Configurez le logging (peut être déplacé dans un fichier de configuration de logging si le projet grandit)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _get_db_connection():
    """Établit et retourne une connexion à la base de données PostgreSQL."""
    try:
        conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT,
            sslmode='verify-full',
            sslrootcert='system' 
        )
        return conn
    except Exception as e:
        logging.error(f"Erreur de connexion à la base de données PostgreSQL : {e}")
        raise # Rélève l'exception pour que les fonctions appelantes la gèrent

def create_reviews_table():
    """Crée la table 'reviews_nickel' si elle n'existe pas dans PostgreSQL."""
    conn = None # Initialiser à None
    try:
        conn = _get_db_connection()
        with conn.cursor() as c: # Utilisation du context manager pour le curseur
            c.execute(config.TABLE_SCHEMA_POSTGRES)
        conn.commit() # Commit la création de table
        logging.info(f"Table 'reviews_nickel' vérifiée/créée dans la base de données PostgreSQL '{config.DB_NAME}'.")
    except Exception as e:
        logging.error(f"Erreur lors de la création de la table : {e}")
        if conn:
            conn.rollback() # Annuler en cas d'erreur
        raise # Rélève l'exception
    finally:
        if conn:
            conn.close() # Ferme la connexion

def insert_review_data(review_data):
    """
    Insère un avis dans la base de données PostgreSQL.
    Gère l'unicité par contenu_hash en utilisant ON CONFLICT.
    Retourne True si l'avis a été inséré/mis à jour, False si le hash est manquant.
    """
    conn = None
    try:
        contenu_hash = review_data.get('contenu_hash')

        if not contenu_hash:
            logging.warning("Impossible d'insérer l'avis : 'contenu_hash' manquant.")
            return False

        conn = _get_db_connection()
        with conn.cursor() as c:
            # Utilisation de ON CONFLICT (contenu_hash) DO NOTHING;
            # Cela insérera si le hash est unique, ou ne fera rien si le hash existe déjà.

                    # --- DÉBUT DES CONVERSIONS DE TYPE (INDISPENSABLE MAINTENANT) ---

            # date_publication (vers datetime.date car votre schema est DATE)
            date_publication_str = review_data.get('date_publication')
            date_publication_obj = None
            if date_publication_str:
                try:
                    # Assurez-vous que le format de date est correct (ex: '2025-07-22')
                    # Si 'YYYY-MM-DD HH:MM:SS', utilisez datetime.strptime(date_publication_str, '%Y-%m-%d %H:%M:%S').date()
                    # Si 'YYYY-MM-DDTHH:MM:SSZ', utilisez datetime.fromisoformat(...).date()
                    # Compte tenu de votre `extract_publication_date` qui renvoie `'%Y-%m-%d %H:%M:%S'`, on doit s'adapter :
                    date_publication_obj = datetime.strptime(date_publication_str, '%Y-%m-%d %H:%M:%S').date()
                except ValueError as ve:
                    logging.warning(f"Impossible de parser date_publication '{date_publication_str}' en DATE: {ve}")

            # date_experience (vers datetime.date car votre schema est DATE)
            date_experience_str = review_data.get('date_experience')
            date_experience_obj = None
            if date_experience_str:
                try:
                    date_experience_obj = datetime.strptime(date_experience_str, '%Y-%m-%d').date()
                except ValueError as ve:
                    logging.warning(f"Impossible de parser date_experience '{date_experience_str}' en DATE: {ve}")

            # date_scraping (vers datetime.datetime car votre schema est TIMESTAMP)
            date_scraping_str = review_data.get('date_scraping')
            date_scraping_obj = None
            if date_scraping_str:
                try:
                    # le scraper mettait déjà %Y-%m-%d %H:%M:%S
                    date_scraping_obj = datetime.strptime(date_scraping_str, '%Y-%m-%d %H:%M:%S')
                except ValueError as ve:
                    logging.warning(f"Impossible de parser date_scraping '{date_scraping_str}' en TIMESTAMP: {ve}")


            # date_reponse (vers datetime.date car le schema est DATE)
            date_reponse_str = review_data.get('date_reponse')
            date_reponse_obj = None
            if date_reponse_str:
                try:
                    # le scraper mettait déjà %Y-%m-%d %H:%M:%S
                    date_reponse_obj = datetime.strptime(date_reponse_str, '%Y-%m-%d %H:%M:%S').date()
                except ValueError as ve:
                    logging.warning(f"Impossible de parser date_reponse '{date_reponse_str}' en DATE: {ve}")

            # Les autres champs (Boolean, INTEGER, VARCHAR, TEXT) ne nécessitent pas de conversion spéciale.
            avis_sur_invitation = review_data.get('avis_sur_invitation')
            reponse = review_data.get('reponse')


            insert_query = """
                INSERT INTO reviews_nickel (nom, nombre_avis, langue_origine, note_avis,
                       date_publication, date_experience, jour_experience, mois_experience,
                      annee_experience, contenu_avis, contenu_hash, avis_sur_invitation,
                       sentiment, reponse, date_reponse, date_scraping)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (contenu_hash, date_publication) DO NOTHING;
            """
            # Les valeurs sont passées sous forme de tuple, psycopg2 gère le mapping des types
            c.execute(insert_query, (
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
            # rowcount sera 1 si une nouvelle ligne a été insérée, 0 si le conflit a empêché l'insertion
            if c.rowcount > 0:
                conn.commit()
                #logging.info(f"Avis avec hash '{contenu_hash}' inséré avec succès.")
                return True
            else:
                logging.info(f"Avis avec hash '{contenu_hash}' est un doublon, insertion ignorée.")
                return False

    except Exception as e:
        logging.error(f"Erreur lors de l'insertion de l'avis avec hash '{review_data.get('contenu_hash')}': {e}")
        if conn:
            conn.rollback() # Annuler en cas d'erreur
        raise # Rélève l'exception
    finally:
        if conn:
            conn.close() # Ferme la connexion


#########################################################
# ######################## sqlite3 ########################
# import sqlite3
# def create_reviews_table():
#    """Crée la table 'reviews_nickel' si elle n'existe pas."""
#    with sqlite3.connect(config.DATABASE_PATH) as conn:
#        c = conn.cursor()
#        c.execute(config.TABLE_SCHEMA)
#        conn.commit()
#    print(f"Table 'reviews_nickel' vérifiée/créée dans {config.DATABASE_PATH}.")

# def insert_review_data(review_data):
#    """
#    Insère un avis dans la base de données.
#    Vérifie l'unicité par contenu_hash avant l'insertion.
#    Retourne True si l'avis a été inséré, False sinon (doublon).
#    """
#    with sqlite3.connect(config.DATABASE_PATH) as conn:
#        c = conn.cursor()
#        contenu_hash = review_data.get('contenu_hash')

#        if contenu_hash: 
#            c.execute("SELECT COUNT(*) FROM reviews_nickel WHERE contenu_hash = ?", (contenu_hash,))
#            if c.fetchone()[0] == 0:
#                c.execute("""
#                    INSERT INTO reviews_nickel (nom, nombre_avis, langue_origine, note_avis, 
#                           date_publication, date_experience, jour_experience, mois_experience, 
#                          annee_experience, contenu_avis, contenu_hash, avis_sur_invitation, 
#                           sentiment, reponse, date_reponse, date_scraping)
#                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                """, (
#                    review_data.get('nom'),
#                    review_data.get('nombre_avis'),
#                    review_data.get('langue_origine'),
#                    review_data.get('note_avis'),
#                    review_data.get('date_publication'),
#                    review_data.get('date_experience'),
#                    review_data.get('jour_experience'),
#                    review_data.get('mois_experience'),
#                    review_data.get('annee_experience'),
#                    review_data.get('contenu_avis'),
#                    review_data.get('contenu_hash'),
#                    review_data.get('avis_sur_invitation'),
#                    review_data.get('sentiment'),
#                    review_data.get('reponse'),
#                    review_data.get('date_reponse'),
#                    review_data.get('date_scraping')
#                ))
#                conn.commit()
#                return True
#        return False # Retourne False si pas de hash ou si doublon

# import logging
# import sqlite3
# def create_reviews_table():
#    """Crée la table 'reviews_nickel' si elle n'existe pas."""
#    try:
#        # Assurez-vous que le dossier 'data' existe
#        import os
#        data_dir = os.path.dirname(config.DATABASE_PATH)
#        if not os.path.exists(data_dir):
#            os.makedirs(data_dir)
#            logging.info(f"Dossier '{data_dir}' créé pour la base de données.")

#        with sqlite3.connect(config.DATABASE_PATH) as conn:
#            c = conn.cursor()
#            c.execute(config.TABLE_SCHEMA)
#            conn.commit()
#        logging.info(f"Table 'reviews_nickel' vérifiée/créée dans {config.DATABASE_PATH}.")
#    except Exception as e:
#        logging.error(f"Erreur lors de la création de la table SQLite: {e}")
#        raise # Relance l'exception pour arrêter le script si la DB ne peut pas être créée

# def insert_review_data(review_data):
#    """
#    Insère un avis dans la base de données.
#    Vérifie l'unicité par contenu_hash avant l'insertion.
#    Retourne True si l'avis a été inséré, False sinon (doublon ou erreur).
#    """
#    conn = None # Initialiser la connexion à None
#    try:
#        conn = sqlite3.connect(config.DATABASE_PATH)
#        c = conn.cursor()
#        contenu_hash = review_data.get('contenu_hash')

#        if contenu_hash:
#            # Vérifie si un avis avec ce hash existe déjà
#            c.execute("SELECT COUNT(*) FROM reviews_nickel WHERE contenu_hash = ?", (contenu_hash,))
#            count = c.fetchone()[0]

#            if count == 0:
#                # Insérer l'avis si le hash est unique
#                c.execute("""
#                    INSERT INTO reviews_nickel (nom, nombre_avis, langue_origine, note_avis,
#                           date_publication, date_experience, jour_experience, mois_experience,
#                          annee_experience, contenu_avis, contenu_hash, avis_sur_invitation,
#                           sentiment, reponse, date_reponse, date_scraping)
#                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                """, (
#                    review_data.get('nom'),
#                    review_data.get('nombre_avis'),
#                    review_data.get('langue_origine'),
#                    review_data.get('note_avis'),
#                    review_data.get('date_publication'),
#                    review_data.get('date_experience'),
#                    review_data.get('jour_experience'),
#                    review_data.get('mois_experience'),
#                    review_data.get('annee_experience'),
#                    review_data.get('contenu_avis'),
#                    review_data.get('contenu_hash'),
#                    review_data.get('avis_sur_invitation'),
#                    review_data.get('sentiment'),
#                    review_data.get('reponse'),
#                    review_data.get('date_reponse'),
#                    review_data.get('date_scraping')
#                ))
#                conn.commit()
#                # logging.info(f"Avis avec hash '{contenu_hash}' inséré avec succès.")
#                return True
#            else:
#                logging.info(f"Avis avec hash '{contenu_hash}' est un doublon, insertion ignorée.")
#                return False
#        else:
#            logging.warning(f"Impossible d'insérer l'avis : 'contenu_hash' manquant pour {review_data.get('nom')}.")
#            return False # Retourne False si pas de hash

#    except sqlite3.IntegrityError as e:
#        logging.error(f"Erreur d'intégrité (doublon de hash) lors de l'insertion pour '{review_data.get('contenu_hash')}': {e}")
#        if conn: conn.rollback()
#        return False
#    except Exception as e:
#        logging.error(f"Erreur inattendue lors de l'insertion de l'avis avec hash '{review_data.get('contenu_hash')}': {e}")
#        if conn: conn.rollback()
#        raise # Relance l'exception pour ne pas masquer les problèmes graves
#    finally:
#        if conn:
#            conn.close() # S'assure que la connexion est fermée