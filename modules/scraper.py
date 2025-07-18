# modules/scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from . import config
from . import review_parser
from . import database

def scrape_page(page_url, current_datetime):
    """
    Scrape une seule page d'avis et extrait les données de chaque avis.
    Retourne une liste de dictionnaires, chaque dictionnaire représentant un avis.
    Args:
        page_url (str): L'URL de la page à scraper.
        current_datetime (datetime): L'heure actuelle pour le timestamp des avis.
    Returns:
        list: Une liste de dictionnaires contenant les données des avis.
    Raises:
        requests.exceptions.RequestException: Si une erreur de requête HTTP se produit.
    """
    print(f"Scraping URL: {page_url}")
    try:
        response = requests.get(page_url, headers={"User-Agent": config.USER_AGENT})
        response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP (4xx ou 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Erreur de requête pour {page_url}: {e}")
        return []

    review_elements = soup.find_all('div', class_='styles_cardWrapper__g8amG styles_show__Z8n7u')
    
    if not review_elements:
        return []

    all_reviews_data = []
    for review_elem in review_elements:
        review_data = {}
        # review_data['date_publication'] = review_parser.extract_publication_date(review_elem, current_datetime)
        review_data['date_publication'] = review_parser.extract_publication_date(review_elem)
        review_data['nom'] = review_parser.extract_reviewer_name(review_elem)
        review_data['nombre_avis'] = review_parser.extract_num_reviews(review_elem)
        review_data['langue_origine'] = review_parser.extract_original_language(review_elem)
        review_data['note_avis'] = review_parser.extract_review_rating(review_elem)
        
        date_exp_str, jour_exp, mois_exp, annee_exp = review_parser.extract_experience_date(review_elem)
        review_data['date_experience'] = date_exp_str
        review_data['jour_experience'] = jour_exp
        review_data['mois_experience'] = mois_exp
        review_data['annee_experience'] = annee_exp
        
        review_data['contenu_avis'] = review_parser.extract_review_content(review_elem)
        review_data['avis_sur_invitation'] = review_parser.extract_invitation_status(review_elem)
        
        review_data['contenu_hash'] = review_parser.generate_content_hash(review_data['contenu_avis'])

        review_data['sentiment'] = review_parser.analyze_sentiment(review_data['note_avis'])
        
        review_data['date_scraping'] = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
        
        review_data['reponse'] = review_parser.reponse(review_elem)
        
        #review_data['date_reponse'] = review_parser.extract_response_date(review_elem, current_datetime)
        review_data['date_reponse'] = review_parser.extract_response_date(review_elem)

        all_reviews_data.append(review_data)
    
    return all_reviews_data

#def run_scraper(max_pages_to_scrape=3): # Pour tester le scraping sur 3 pages
def run_scraper():
    """
    Fonction principale pour orchestrer le processus de scraping complet.
    Retourne une chaîne de caractères récapitulative du scraping.
    """
    database.create_reviews_table()

    page = 1
    total_new_reviews = 0
    added_reviews_summary = [] # liste pour stocker les résumés des avis ajoutés
    
    #while page <= max_pages_to_scrape: #pour tester le scraping sur 3 pages
    while True:
        current_datetime_for_scraping = datetime.now()

        page_url = f"{config.BASE_URL}{page}"
        reviews_on_page = scrape_page(page_url, current_datetime_for_scraping)

        if not reviews_on_page:
            #print(f"Plus d'avis trouvés après la page {page - 1}, arrêt du scraping.") # Déplacé dans le message final
            break

        for review in reviews_on_page:
            if database.insert_review_data(review):
                total_new_reviews += 1
                # Ajoute un résumé de l'avis à la liste
                summary = (
                    f"  - Nom: {review.get('nom', 'N/A')}, "
                    f"Date Pub: {review.get('date_publication', 'N/A')}, "
                    f"Contenu (extrait): {review.get('contenu_avis', 'N/A')[:50]}..." # Extrait les 50 premiers caractères
                )
                added_reviews_summary.append(summary)
        
        page += 1
        time.sleep(config.SLEEP_TIME)

    # Construction de la chaîne de caractères finale
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