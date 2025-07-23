# modules/scraper.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import logging

from . import config
from . import review_parser
from . import database

# Configure le logging pour le module scraper
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def scrape_page(page_url, current_datetime):
    """
    Gratte une seule page d'avis et extrait les données pertinentes.

    Args:
        page_url (str): L'URL de la page à scraper.
        current_datetime (datetime): L'horodatage actuel pour la date de scraping.

    Returns:
        list: Une liste de dictionnaires, où chaque dictionnaire représente un avis.
              Retourne une liste vide en cas d'erreur ou si aucun avis n'est trouvé.
    """
    logging.info(f"Scraping URL: {page_url}")
    try:
        response = requests.get(page_url, headers={"User-Agent": config.USER_AGENT})
        response.raise_for_status()  # Lève une exception pour les codes d'état HTTP d'erreur
        soup = BeautifulSoup(response.text, 'lxml') # Utiliser lxml pour de meilleures performances si installé
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur de requête pour {page_url}: {e}")
        return []

    review_container_elements = soup.find_all('div', class_='styles_cardWrapper__g8amG styles_show__Z8n7u')

    if not review_container_elements:
        logging.info(f"Aucun conteneur d'avis trouvé sur {page_url} avec la classe spécifiée.")
        return []

    all_reviews_data = []
    for review_container_elem in review_container_elements:
        # Chaque conteneur doit contenir une balise <article>
        review_soup_article = review_container_elem.find('article')

        if not review_soup_article:
            logging.warning("Balise <article> non trouvée dans un conteneur d'avis. Ignoré.")
            continue

        review_data = {}
        # Extraction des données en utilisant les fonctions de review_parser
        review_data['date_publication'] = review_parser.extract_publication_date(review_soup_article)
        review_data['nom'] = review_parser.extract_reviewer_name(review_soup_article)
        review_data['nombre_avis'] = review_parser.extract_num_reviews(review_soup_article)
        review_data['langue_origine'] = review_parser.extract_original_language(review_soup_article)
        review_data['note_avis'] = review_parser.extract_review_rating(review_soup_article)
        
        # Extraction de la date d'expérience et de ses composants
        date_exp_str, jour_exp, mois_exp, annee_exp = review_parser.extract_experience_date(review_soup_article)
        review_data['date_experience'] = date_exp_str
        review_data['jour_experience'] = jour_exp
        review_data['mois_experience'] = mois_exp
        review_data['annee_experience'] = annee_exp
        
        review_data['contenu_avis'] = review_parser.extract_review_content(review_soup_article)
        review_data['avis_sur_invitation'] = review_parser.extract_invitation_status(review_soup_article)
        
        review_data['contenu_hash'] = review_parser.generate_content_hash(review_soup_article)

        # Sentiment basé sur la note de l'avis
        review_data['sentiment'] = review_parser.analyze_sentiment(review_data['note_avis'])

        review_data['date_scraping'] = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
        
        review_data['reponse'] = review_parser.reponse(review_soup_article)
        review_data['date_reponse'] = review_parser.extract_response_date(review_soup_article)

        all_reviews_data.append(review_data)
    
    return all_reviews_data

#def run_scraper(max_pages_to_scrape=3): # scraping sur 3 pages pour les tests
def run_scraper(): # Pour scraper toutes les pages
    database.create_reviews_table()

    page = 1
    total_new_reviews = 0
    added_reviews_summary = []
    
    #while page <= max_pages_to_scrape: # pour tester le scraping sur 3 pages
    while True:
        current_datetime_for_scraping = datetime.now()

        page_url = f"{config.BASE_URL}{page}" # Correction: config.BASE_URL doit déjà contenir "?page="
        reviews_on_page = scrape_page(page_url, current_datetime_for_scraping)

        if not reviews_on_page:
            logging.info(f"Plus d'avis trouvés sur la page {page}, arrêt du scraping.")
            break

        for review in reviews_on_page:
            # Vérifier que le hash est bien généré avant l'insertion
            if review.get('contenu_hash') is None:
                logging.warning(f"Impossible d'insérer l'avis : 'contenu_hash' manquant pour {review.get('nom', 'N/A')}.")
                continue # Passe à l'avis suivant si le hash est manquant

            if database.insert_review_data(review):
                total_new_reviews += 1
                summary = (
                    f"  - Nom: {review.get('nom', 'N/A')}, "
                    f"Date Pub: {review.get('date_publication', 'N/A')}, "
                    f"Contenu (extrait): {review.get('contenu_avis', 'N/A')[:50]}..."
                )
                added_reviews_summary.append(summary)
        
        page += 1
        time.sleep(config.SLEEP_TIME)

    if not reviews_on_page and page > 1: 
        final_message = f"Scraping terminé car plus d'avis trouvés après la page {page - 1}.\n"
    else:
        final_message = "Scraping terminé.\n"

    final_message += f"{total_new_reviews} nouveaux avis ajoutés à la base de données.\n"

    if added_reviews_summary:
        final_message += "\nDétail des nouveaux avis ajoutés :\n"
        final_message += "\n".join(added_reviews_summary[:10]) 
        if len(added_reviews_summary) > 10:
            final_message += "\n  (Affichage limité aux 10 premiers avis ajoutés...)"
    else:
        final_message += "Aucun nouvel avis n'a été ajouté cette fois-ci."

    return final_message