# Projet de Scraping Trustpilot - Avis Nickel.eu

Ce projet Python est un scraper modulaire conçu pour extraire les avis de la page Trustpilot de Nickel.eu et les stocker dans une base de données SQLite. Il est structuré pour être facilement maintenable, extensible et pour fournir un rapport clair après chaque exécution.

## Table des matières
### Structure du Projet

### Prérequis

### Installation

### Utilisation du Script

### Configuration des Paramètres

### Ajouter une Nouvelle Colonne / Extraire de Nouvelles Données

### Gestion des Erreurs Courantes

## 1. Structure du Projet

Le projet est organisé comme suit :

projet3_scraping/
├── data/
│   └── sqlite_reviews_nickel.db  # Base de données SQLite des avis (sera créée si elle n'existe pas)
├── modules/
│   ├── __init__.py               # Fichier vide qui marque 'modules' comme un paquet Python
│   ├── config.py                 # Contient toutes les constantes de configuration du scraper
│   ├── database.py               # Gère les interactions avec la base de données SQLite (création de table, insertion)
│   ├── review_parser.py          # Fonctions dédiées à l'extraction et à la transformation des données d'un avis individuel
│   └── scraper.py                # Contient la logique de navigation, l'orchestration du scraping par page et le rapport final
└── main.py                     # Le point d'entrée principal pour lancer le scraping
└── README.md                   # Ce fichier d'information

## 2. Prérequis
Assurez-vous d'avoir Python 3.x installé sur votre système.

## 3. Installation
Naviguez dans le répertoire racine du projet projet3_scraping via votre terminal :

cd /chemin/vers/votre/projet3_scraping


Créez un environnement virtuel (recommandé pour isoler les dépendances du projet) :

python3 -m venv .venv


Activez l'environnement virtuel :

Sur macOS/Linux:

source .venv/bin/activate

Sur Windows (Command Prompt):

.venv\Scripts\activate.bat

Sur Windows (PowerShell):

.venv\Scripts\Activate.ps1

Installez les bibliothèques Python nécessaires :

pip install requests beautifulsoup4

## 4. Utilisation du Script
Pour lancer le scraping des avis, exécutez simplement le script main.py depuis le répertoire racine du projet projet3_scraping.

python main.py

Le script se connectera à Trustpilot, extraira les avis et les enregistrera dans le fichier data/sqlite_reviews_nickel.db. Des messages de progression et un rapport détaillé des avis ajoutés seront affichés dans la console.

Démarrage du processus de scraping...

Scraping URL: https://fr.trustpilot.com/review/nickel.eu?page=1
Scraping URL: https://fr.trustpilot.com/review/nickel.eu?page=2
Scraping URL: https://fr.trustpilot.com/review/nickel.eu?page=3

==================================================
RAPPORT DE SCRAPING
==================================================
Scraping terminé.
X nouveaux avis ajoutés à la base de données.

Détail des nouveaux avis ajoutés :
  - Nom: John Doe, Date Pub: 2023-01-15 10:30, Contenu (extrait): Excellent service, très rapide et efficace. J...
  - Nom: Jane Smith, Date Pub: 2024-03-20 14:00, Contenu (extrait): Je suis déçue, j'ai eu des problèmes avec l'...
  (Affichage limité aux 10 premiers avis ajoutés...)
==================================================

## 5. Configuration des Paramètres
Tous les paramètres configurables se trouvent dans le fichier modules/config.py.


modules/config.py

DATABASE_PATH = 'data/sqlite_reviews_nickel.db'
BASE_URL = "https://fr.trustpilot.com/review/nickel.eu?page="
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
SLEEP_TIME = 2 # Secondes de pause entre chaque page

MOIS_MAPPING = {
    'janvier': 'January', 'février': 'February', 'mars': 'March',
    'avril': 'April', 'mai': 'May', 'juin': 'June',
    'juillet': 'July', 'août': 'August', 'septembre': 'September',
    'octobre': 'October', 'novembre': 'November', 'décembre': 'December',
    'janv.': 'January', 'févr.': 'February', 'mars.': 'March',
    'avr.': 'April', 'mai.': 'May', 'juin.': 'June',
    'juil.': 'July', 'août.': 'August', 'sept.': 'September',
    'oct.': 'October', 'nov.': 'November', 'dec.': 'December',
    'aout': 'August' # Pour gérer 'août' sans accent
}

TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews_nickel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_publication TEXT,
    nom VARCHAR(30),
    nombre_avis INTEGER,
    langue_origine CHAR(3),
    note_avis INTEGER,
    date_experience TEXT,
    jour_experience INTEGER,
    mois_experience INTEGER,
    annee_experience INTEGER,
    contenu_avis TEXT,
    contenu_hash TEXT UNIQUE,
    avis_sur_invitation BOOLEAN,
    date_scraping DATETIME
)
"""
**DATABASE_PATH**: Le chemin où le fichier de la base de données SQLite sera créé ou recherché. Il est actuellement défini pour placer la base de données dans le dossier data/ à la racine du projet.

**BASE_URL**: L'URL de base de Trustpilot à scraper.

**USER_AGENT**: L'en-tête User-Agent envoyé avec les requêtes HTTP. Il est recommandé d'utiliser un User-Agent courant pour éviter d'être bloqué.

**SLEEP_TIME**: Le délai (en secondes) entre le scraping de chaque page. Cela permet d'éviter de surcharger le serveur et de réduire le risque d'être détecté comme un bot.

**MOIS_MAPPING**: Dictionnaire utilisé pour convertir les noms de mois en français (et leurs abréviations) en anglais pour une bonne interprétation des dates.

**TABLE_SCHEMA**: La définition SQL de la table de la base de données. Modifiez-la si vous ajoutez ou changez des colonnes.

De plus, dans main.py, vous pouvez spécifier le nombre maximal de pages à scraper :


#main.py
#...
if __name__ == "__main__":
    print("Démarrage du processus de scraping...\n")
    # Scrape les 3 premières pages par défaut. Changez ce nombre selon vos besoins.
    scraping_report = run_scraper(max_pages_to_scrape=3)
    print("\n" + "="*50)
    print("RAPPORT DE SCRAPING")
    print("="*50)
    print(scraping_report)
    print("="*50)

Changez max_pages_to_scrape à la valeur souhaitée. Si vous voulez scraper toutes les pages disponibles jusqu'à ce qu'il n'y ait plus d'avis, vous pouvez passer float('inf') (utilisez cette option avec prudence, car cela peut prendre beaucoup de temps et solliciter fortement le serveur cible).

## 6. Ajouter une Nouvelle Colonne / Extraire de Nouvelles Données
Pour étendre les capacités de scraping et extraire de nouvelles données, suivez ces étapes :

#### Étape 1: Mettre à jour le Schéma de la Base de Données

Ouvrez modules/config.py.

Modifiez la constante TABLE_SCHEMA pour ajouter votre nouvelle colonne, en respectant le type de données SQLite.

Exemple : Si vous voulez ajouter une colonne source_url de type TEXT.

#modules/config.py

TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews_nickel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- ... vos colonnes existantes ...
    source_url TEXT, -- Nouvelle colonne ajoutée
    date_scraping DATETIME
)
"""

**Important concernant les bases de données existantes** :
Le CREATE TABLE IF NOT EXISTS ne modifiera pas une table déjà existante.

Pour le développement rapide : Si votre base de données (data/sqlite_reviews_nickel.db) ne contient pas encore de données importantes, la solution la plus simple est de supprimer manuellement le fichier sqlite_reviews_nickel.db. Le script le recréera avec le nouveau schéma lors de la prochaine exécution.

Pour la production : Pour des bases de données existantes avec des données précieuses, l'ajout de colonnes se fait via des scripts de migration (ALTER TABLE ADD COLUMN). Cette opération est plus complexe et dépasse le cadre de ce README.

#### Étape 2: Créer la Fonction d'Extraction

Ouvrez modules/review_parser.py.

Ajoutez une nouvelle fonction dédiée à l'extraction de la donnée souhaitée. Cette fonction doit prendre soup_avis (le fragment BeautifulSoup correspondant à un avis individuel) en argument et retourner la donnée extraite (ex: une chaîne de caractères, un entier) ou None si la donnée ne peut pas être trouvée.

Exemple : Extraction de l'URL complète de l'avis.

#modules/review_parser.py
#... (vos imports et autres fonctions d'extraction) ...

def extract_review_url(soup_avis):
    """Extrait l'URL complète de l'avis si disponible."""
    try:
        # Adaptez ce sélecteur CSS (par exemple, 'a.styles_reviewLink__J_V40')
        # en fonction de la structure HTML actuelle de Trustpilot.
        link_element = soup_avis.find('a', class_='styles_reviewLink__J_V40')
        if link_element and 'href' in link_element.attrs:
            relative_url = link_element['href']
            # Construisez l'URL absolue si Trustpilot fournit des chemins relatifs
            return f"https://fr.trustpilot.com{relative_url}"
        return None
    except AttributeError:
        return None

#### Étape 3: Intégrer la Nouvelle Colonne dans le Scraper

Ouvrez modules/scraper.py.

Dans la fonction scrape_page, localisez la boucle for review_elem in review_elements:.

Appelez votre nouvelle fonction d'extraction et stockez le résultat dans le dictionnaire review_data avec la clé correspondant au nom de votre colonne.

Exemple :

#modules/scraper.py
#...
def scrape_page(page_url, current_datetime):
    # ...
    for review_elem in review_elements:
        review_data = {}
        # ... (vos extractions existantes) ...
        review_data['contenu_avis'] = review_parser.extract_review_content(review_elem)

        # Appel de la nouvelle fonction d'extraction et assignation
        review_data['source_url'] = review_parser.extract_review_url(review_elem) # Nouvelle ligne à ajouter

        review_data['avis_sur_invitation'] = review_parser.extract_invitation_status(review_elem)
        # ...
        all_reviews_data.append(review_data)
    return all_reviews_data

#### Étape 4: Mettre à jour la Fonction d'Insertion en Base de Données

Ouvrez modules/database.py.

Dans la fonction insert_review_data, vous devez :

Ajouter le nom de la nouvelle colonne à la liste des colonnes dans la requête INSERT INTO.

Ajouter un placeholder ? correspondant dans la section VALUES.

Ajouter la nouvelle donnée (récupérée via review_data.get('votre_nouvelle_colonne')) au tuple de valeurs passé à c.execute(), en respectant l'ordre.

#modules/database.py
#...

def insert_review_data(review_data):
    # ...
    if contenu_hash:
        c.execute("SELECT COUNT(*) FROM reviews_nickel WHERE contenu_hash = ?", (contenu_hash,))
        if c.fetchone()[0] == 0:
            c.execute("""
                INSERT INTO reviews_nickel (nom, date_publication, nombre_avis, langue_origine, note_avis, date_experience, jour_experience, mois_experience, annee_experience, contenu_avis, contenu_hash, avis_sur_invitation, source_url, date_scraping) -- Nouvelle colonne ici
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) -- Ajout d'un placeholder
            """, (
                review_data.get('nom'),
                review_data.get('date_publication'),
                review_data.get('nombre_avis'),
                review_data.get('langue_origine'),
                review_data.get('note_avis'),
                review_data.get('date_experience'),
                review_data.get('jour_experience'),
                review_data.get('mois_experience'),
                review_data.get('annee_experience'),
                review_data.get('contenu_avis'),
                review_data.get('contenu_hash'),
                review_data.get('avis_sur_invitation'),
                review_data.get('source_url'), # Nouvelle donnée ici
                review_data.get('date_scraping')
            ))
            conn.commit()
            return True
        return False
    return False
Étape 5: Tester

Après avoir effectué ces modifications et potentiellement recréé la base de données (si nécessaire), exécutez python main.py. Le script devrait maintenant extraire et enregistrer la nouvelle donnée dans la colonne correspondante de votre base de données.

#### 7. Gestion des Erreurs Courantes
sqlite3.OperationalError: unable to open database file

Cause : Ce message indique généralement un problème de chemin d'accès à la base de données ou de permissions.

Solution :

Vérifiez modules/config.py : Assurez-vous que DATABASE_PATH = 'data/sqlite_reviews_nickel.db' est correctement défini (sans ../).

Vérifiez l'existence du dossier data : Le script essaiera de créer le fichier .db mais pas le dossier parent data/. Si le dossier data n'existe pas dans le répertoire projet3_scraping/, créez-le manuellement ou assurez-vous que la ligne os.makedirs(db_dir, exist_ok=True) dans modules/database.py est présente et fonctionnelle.

Permissions : Assurez-vous que le script a les droits d'écriture dans le répertoire data/ et les droits de lecture/écriture sur le fichier sqlite_reviews_nickel.db si ce dernier existe déjà.

requests.exceptions.RequestException ou problèmes de connexion

Cause : Problèmes de réseau, l'URL est incorrecte, ou le site cible a bloqué votre requête (souvent dû à un nombre trop élevé de requêtes ou à un User-Agent non reconnu).

Solution :

Vérifiez votre connexion Internet.

Vérifiez BASE_URL dans modules/config.py pour s'assurer qu'il est correct.

Ajustez SLEEP_TIME dans modules/config.py pour augmenter le délai entre les requêtes.

Changez le USER_AGENT dans modules/config.py pour un User-Agent plus courant (vous pouvez le trouver en cherchant "my user agent" dans un navigateur).

AttributeError: 'NoneType' object has no attribute 'find' (ou similaire lié à BeautifulSoup)

Cause : Cela signifie que BeautifulSoup n'a pas trouvé l'élément HTML qu'il cherchait (le find() ou find_all() est revenu None), et vous avez ensuite essayé d'accéder à un attribut ou d'appeler une méthode sur ce None. C'est souvent dû à un changement dans la structure HTML du site web cible ou à un sélecteur CSS incorrect.

Solution :

Inspectez le code source HTML de la page Trustpilot (via les outils de développement de votre navigateur) pour les éléments que vous essayez de scraper.

Mettez à jour les sélecteurs CSS (les class_, id, etc.) dans les fonctions extract_... de modules/review_parser.py pour qu'ils correspondent à la structure actuelle du site. Les sites web peuvent changer leur structure HTML, ce qui nécessite une mise à jour de vos sélecteurs.