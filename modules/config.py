# config.py

BASE_URL = "https://fr.trustpilot.com/review/nickel.eu?page="
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
SLEEP_TIME = 1

######################################

# --- SCHEMA DE TABLE POSTGRESQL ---
# Notez les changements de types et de syntaxe (SERIAL, VARCHAR, TIMESTAMP, etc.)
TABLE_SCHEMA_POSTGRES = """
CREATE TABLE IF NOT EXISTS reviews_nickel (
    id SERIAL PRIMARY KEY,              -- AUTOINCREMENT devient SERIAL
    reponse BOOLEAN,
    date_reponse TIMESTAMP,                  -- TIMESTAMP pour la date de réponse (précédemment TEXT)
    date_publication TIMESTAMP,              -- TIMESTAMP pour la date de publication (précédemment TEXT)
    nom VARCHAR(255),                   -- VARCHAR avec une taille max plus généreuse pour les noms
    nombre_avis INTEGER,
    langue_origine CHAR(50),
    note_avis INTEGER,
    date_experience DATE,               -- (précédemment TEXT)
    jour_experience INTEGER,
    mois_experience INTEGER,
    annee_experience INTEGER,
    contenu_avis TEXT,
    contenu_hash VARCHAR(64)        ,  -- VARCHAR pour le hash de contenu
    avis_sur_invitation BOOLEAN,
    sentiment VARCHAR(15),            -- VARCHAR pour le sentiment
    date_scraping TIMESTAMP,                -- DATETIME devient TIMESTAMP
    UNIQUE (contenu_hash, date_publication)            
);
"""

###### bdd sqlite3 #######
# #DATABASE_PATH = 'data/sqlite_reviews_nickel.db'
# DATABASE_PATH = 'data/TEST.db' # Pour les tests
# TABLE_SCHEMA = """
# CREATE TABLE IF NOT EXISTS reviews_nickel (
#    id INTEGER PRIMARY KEY AUTOINCREMENT,
#    reponse BOOLEAN,
#    date_reponse TEXT,
#    date_publication TEXT,
#    nom VARCHAR(30),
#    nombre_avis INTEGER,
#    langue_origine CHAR(3),
#    note_avis INTEGER,
#    date_experience TEXT,
#    jour_experience INTEGER,
#    mois_experience INTEGER,
#    annee_experience INTEGER,
#    contenu_avis TEXT,
#    contenu_hash TEXT UNIQUE,
#    avis_sur_invitation BOOLEAN,
#    sentiment TEXT,
#    date_scraping DATETIME
# )
# """


# configuration des mois pour l'extraction des dates
MOIS_MAPPING = {
    'janvier': 'January', 'février': 'February', 'mars': 'March',
    'avril': 'April', 'mai': 'May', 'juin': 'June',
    'juillet': 'July', 'août': 'August', 'septembre': 'September',
    'octobre': 'October', 'novembre': 'November', 'décembre': 'December',
    'janv.': 'January', 'févr.': 'February', 'mars.': 'March', 
    'avr.': 'April', 'mai.': 'May', 'juin.': 'June',
    'juil.': 'July', 'août.': 'August', 'sept.': 'September',
    'oct.': 'October', 'nov.': 'November', 'dec.': 'December',
    'aout': 'August'
}