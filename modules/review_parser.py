# review_parser.py
import re
from datetime import datetime, timedelta
import hashlib
from . import config 

def extract_publication_date(review_soup_article):
    """
    Scrape la date absolue d'un objet BeautifulSoup représentant un avis
    et la nettoie au format 'YYYY-MM-DD HH:MM:SS'.

    Args:
        review_soup_article (bs4.Tag): Un objet BeautifulSoup représentant
                                        une balise <article> d'avis individuelle.

    Returns:
        str or None: La date formatée si trouvée et convertie avec succès,
                     sinon None.
    """
    try:
        rectangle = review_soup_article.find('div', class_='styles_reviewCardInnerHeader__8Xqy8')
        
        if not rectangle:
            return None

        div_time = rectangle.find('div', class_='typography_body-m__k2UI7 typography_appearance-subtle__PYOVM')
        
        if not div_time:
            return None

        time_tag = div_time.find('time')
        
        if not time_tag:
            return None 

        absolute_date_raw = time_tag.get('datetime')

        if not absolute_date_raw:
            return None

        dt_object = datetime.strptime(absolute_date_raw, '%Y-%m-%dT%H:%M:%S.%fZ')
        
        formatted_date = dt_object.strftime('%Y-%m-%d %H:%M:%S')
        
        return formatted_date

    except (AttributeError, ValueError) as e:
        f"Erreur lors de l'extraction/formatage de la date de publication : {e}"
        return None


def extract_reviewer_name(soup_avis):
    """Extrait le nom de l'utilisateur.
    Retourne le nom de l'utilisateur ou None si non trouvé."""
    try:
        return soup_avis.find('span', class_='typography_heading-xs__osRhC typography_appearance-default__t8iAq styles_consumerName__xKr9c').text.strip()
    except AttributeError:
        return None

def extract_num_reviews(soup_avis):
    """Extrait le nombre d'avis de l'utilisateur.
    Retourne un entier ou None si non trouvé."""
    try:
        sub_spans = soup_avis.find_all('span', class_='typography_body-m__k2UI7 typography_appearance-subtle__PYOVM')
        if len(sub_spans) >= 2:
            raw_nombre_avis = sub_spans[1].text.strip()
            match = re.search(r'(\d+)', raw_nombre_avis)
            return int(match.group(1)) if match else None
        return None
    except Exception as e:
        print(f"Erreur lors de l'extraction de nombre_avis : {e}")
        return None

def extract_original_language(soup_avis):
    """Extrait la langue d'origine de l'avis.
    Retourne le code de langue (2 ou 3 lettres) ou None si non trouvé."""
    try:
        span = soup_avis.find('span', class_="typography_body-m__k2UI7 typography_appearance-subtle__PYOVM")
        if span and "langue d'origine" in span.text.lower():
            match = re.search(r'Langue d\'origine : ([a-zA-Z]{2,3})', span.text)
            if match:
                return match.group(1)
        return span.text.strip() if span else None
    except AttributeError:
        return None

def extract_review_rating(soup_avis):
    """Extrait la note de l'avis.
    Retourne un entier de 1 à 5 ou None si non trouvé."""
    try:
        return int(soup_avis.find('div', class_="star-rating_starRating__sdbkn star-rating_medium__Oj7C9").img['alt'][5])
    except (AttributeError, IndexError, ValueError):
        return None

def extract_experience_date(soup_avis):
    """
    Extrait et convertit la date de l'expérience, puis ses composants.
    Retourne un tuple (date_experience_str, jour, mois, annee) ou (None, None, None, None).
    """
    try:
        sub_spans = soup_avis.find_all('span', class_='typography_body-m__k2UI7 typography_appearance-subtle__PYOVM')
        if len(sub_spans) >= 2:
            raw_date_experience = sub_spans[2].text.strip()
            date_experience_dt = None

            date_str_temp = raw_date_experience.replace("Date de l'expérience : ", "").strip()

            # Utilisation du MOIS_MAPPING de config.py
            for fr_mois, en_mois in config.MOIS_MAPPING.items():
                date_str_temp = date_str_temp.replace(fr_mois, en_mois)

            try:
                date_experience_dt = datetime.strptime(date_str_temp, '%d %B %Y')

                jour_experience = date_experience_dt.day
                mois_experience = date_experience_dt.month
                annee_experience = date_experience_dt.year

                date_experience = date_experience_dt.strftime('%Y-%m-%d')

                return date_experience, jour_experience, mois_experience, annee_experience

            except ValueError as ve:
                print(f"Erreur de conversion de date pour l'expérience '{raw_date_experience}': {ve}")
                return None, None, None, None
        return None, None, None, None
    except Exception as e:
        print(f"Erreur lors de l'extraction ou conversion de date_experience : {e}")
        return None, None, None, None

def extract_review_content(soup_avis):
    """Extrait le contenu de l'avis.
        Retourne le texte de l'avis ou None si non trouvé."""
    try:
        return soup_avis.find('p', class_='typography_body-l__v5JLj typography_appearance-default__t8iAq').text.strip()
    except AttributeError:
        return None

def extract_invitation_status(soup_avis):
    """Vérifie si l'avis est sur invitation.
    Retourne True si l'avis est sur invitation, sinon False."""
    try:
        details_div = soup_avis.find('div', class_='typography_body-m__k2UI7 typography_appearance-subtle__PYOVM styles_detailsIcon__n1OXF')
        if details_div:
            button_span = details_div.find('span', {'role': 'button'})
            if button_span:
                invitation_span = button_span.find('span')
                if invitation_span and "sur invitation" in invitation_span.get_text(strip=True).lower():
                    return True
        return False
    except Exception:
        return False
    

def reponse(soup_avis):
    """
    Vérifie si l'avis a une réponse de l'entreprise.
    Retourne True si une réponse est présente, sinon False."""
    try:
        company_reply_div = soup_avis.find('div', class_='styles_content__eJmhl')
        result = bool(company_reply_div)
        return result
    except Exception as e:
        return False

def extract_response_date(review_soup_article):
    """
    Extrait la date de réponse de l'entreprise à l'avis.
    Retourne la date formatée ou None si non trouvée.
    """
    try:
        div_reply_info = review_soup_article.find('div', class_='styles_replyInfo__41_in')
        
        if not div_reply_info:
            return None

        time_tag = div_reply_info.find('time')
        
        if not time_tag:
            return None 

        absolute_date_raw = time_tag.get('datetime')

        if not absolute_date_raw:
            return None

        dt_object = datetime.strptime(absolute_date_raw, '%Y-%m-%dT%H:%M:%S.%fZ')
        
        formatted_date = dt_object.strftime('%Y-%m-%d %H:%M:%S')
        
        return formatted_date

    except (AttributeError, ValueError) as e:
        f"Erreur lors de l'extraction/formatage de la date de réponse : {e}"
        return None


def generate_content_hash(content):
    """Génère un hash MD5 pour le contenu de l'avis."""
    if content:
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    return None

def analyze_sentiment(rating):
    """
    Détermine le sentiment de l'avis basé sur sa note.
    1 et 2 = Négatif
    3 = Neutre
    4 et 5 = Positif
    Retourne None si la note est invalide ou manquante.
    """
    if rating is None:
        return None
    
    try:
        rating = int(rating)
        if rating in [1, 2]:
            return "Négatif"
        elif rating == 3:
            return "Neutre"
        elif rating in [4, 5]:
            return "Positif"
        else:
            return None 
    except ValueError:
        return None