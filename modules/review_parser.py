# review_parser.py
import re
from datetime import datetime, timedelta
import hashlib
import logging
from . import config 


def extract_publication_date(review_soup_article):
    """
    Extrait la date de publication en utilisant le XPath.
    XPath: article/div/div[1]/div/time
    """
    try:
        div1 = review_soup_article.find('div', recursive=False)
        if div1:
            div2 = div1.find('div', recursive=False)
            if div2:
                div3 = div2.find('div', recursive=False)
                if div3:
                    time_tag = div3.find('time', recursive=False)
                    if time_tag and 'datetime' in time_tag.attrs:
                        date_str = time_tag['datetime']
                        try:
                            # Trustpilot utilise un format ISO 8601 complet, y compris les millisecondes et le Z (UTC)
                            dt_object = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                            formatted_date = dt_object.strftime("%Y-%m-%d %H:%M:%S")
                            return formatted_date
                        except ValueError:
                            logging.warning(f"Impossible de parser la date '{date_str}' au format attendu. Retourne la date brute.")
                            return date_str # Retourne la date brute si le parsing échoue
        return None
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction de la date de publication: {e}")
        return None


def extract_reviewer_name(review_soup_article):
    """
    Extrait le nom de l'utilisateur.
    """
    try:
        name_span = review_soup_article.select_one('div > div:nth-of-type(1) > aside > div > a > span')
        if name_span:
            return name_span.text.strip()
        return None
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction du nom de l'évaluateur: {e}")
        return None

# def extract_num_reviews(review_soup_article):
#     """Extrait le nombre d'avis de l'utilisateur.
#     Retourne un entier ou None si non trouvé."""
#     try:
#         sub_spans = review_soup_article.find_all('span', class_='typography_body-m__k2UI7 typography_appearance-subtle__PYOVM')
#         if len(sub_spans) >= 2:
#             raw_nombre_avis = sub_spans[1].text.strip()
#             match = re.search(r'(\d+)', raw_nombre_avis)
#             return int(match.group(1)) if match else None
#         return None
#     except Exception as e:
#         print(f"Erreur lors de l'extraction de nombre_avis : {e}")
#         return None

import re
import logging # Assurez-vous que logging est importé en haut de review_parser.py

def extract_num_reviews(review_soup_article):
    """
    Extrait le nombre d'avis de l'utilisateur.
    Retourne un entier ou None si non trouvé.
    """
    try:
        # Cible le span directement en utilisant son attribut data-unique.
        # C'est le moyen le plus fiable compte tenu de l'extrait HTML fourni.
        num_reviews_span = review_soup_article.select_one(
            'span[data-consumer-reviews-count-typography="true"]'
        )
        
        if num_reviews_span:
            # Récupère le contenu texte. BeautifulSoup.text gérera le commentaire HTML ()
            # en le supprimant ou en l'ignorant lors de la concaténation du texte.
            raw_nombre_avis = num_reviews_span.text.strip()
            
            # L'HTML contient "1avis". Le .text donnera "1 avis".
            # La regex est conçue pour gérer d'éventuels espaces supplémentaires.
            match = re.search(r'(\d+)\s*avis', raw_nombre_avis)
            
            if match:
                return int(match.group(1))
            else:
                logging.warning(f"Le texte du span extrait '{raw_nombre_avis}' n'a pas le format 'X avis' attendu pour le compte d'avis.")
                return None
        
        logging.debug("Impossible de trouver le span avec l'attribut data-consumer-reviews-count-typography pour le compte d'avis.")
        return None
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction du nombre d'avis: {e}")
        return None

def extract_original_language(review_soup_article):
    """Extrait la langue d'origine de l'avis.
    Retourne le code de langue (2 ou 3 lettres) ou None si non trouvé."""
    try:
        span = review_soup_article.select_one('span[data-consumer-country-typography="true"]')
        if span and "langue d'origine" in span.text.lower():
            match = re.search(r'Langue d\'origine : ([a-zA-Z]{2,3})', span.text)
            if match:
                return match.group(1)
        return span.text.strip() if span else None
    except AttributeError:
        return None

# def extract_review_rating(review_soup_article):
#     """Extrait la note de l'avis.
#     Retourne un entier de 1 à 5 ou None si non trouvé."""
#     try:
#         return int(review_soup_article.find('div', class_="star-rating_starRating__sdbkn star-rating_medium__Oj7C9").img['alt'][5])
#     except (AttributeError, IndexError, ValueError):
#         return None

def extract_review_rating(review_soup_article):
    """
    Extrait la note de l'avis (un entier de 1 à 5) à partir de l'attribut 'alt' de l'image des étoiles.
    Retourne l'entier ou None si non trouvé ou en cas d'erreur.
    """
    try:
        
        # Option 1: Cibler l'image img avec un alt qui ressemble à notre cible
        star_img = review_soup_article.select_one('img[alt*=" sur 5 étoiles"]')
        
        if star_img and 'alt' in star_img.attrs:
            alt_text = star_img['alt']
            # Utiliser une expression régulière pour extraire le chiffre.
            # Elle recherche "Noté X sur 5 étoiles" et capture X.
            match = re.search(r'Noté (\d+) sur 5 étoiles', alt_text)
            if match:
                return int(match.group(1))
            else:
                logging.warning(f"Texte 'alt' des étoiles trouvé ('{alt_text}') mais le format n'est pas 'Noté X sur 5 étoiles'.")
                return None
        
        logging.debug("Impossible de trouver l'image d'étoiles avec un attribut 'alt' pertinent pour la note de l'avis.")
        return None
    
    except Exception as e:
        # Capture toutes les erreurs (AttributeError, IndexError, ValueError) de manière générique
        logging.error(f"Erreur lors de l'extraction de la note de l'avis: {e}")
        return None

# def extract_experience_date(review_soup_article):
#     """
#     Extrait et convertit la date de l'expérience, puis ses composants.
#     Retourne un tuple (date_experience_str, jour, mois, annee) ou (None, None, None, None).
#     """
#     try:
#         sub_spans = review_soup_article.find_all('span', class_='typography_body-m__k2UI7 typography_appearance-subtle__PYOVM')
#         if len(sub_spans) >= 2:
#             raw_date_experience = sub_spans[2].text.strip()
#             date_experience_dt = None

#             date_str_temp = raw_date_experience.replace("Date de l'expérience : ", "").strip()

#             # Utilisation du MOIS_MAPPING de config.py
#             for fr_mois, en_mois in config.MOIS_MAPPING.items():
#                 date_str_temp = date_str_temp.replace(fr_mois, en_mois)

#             try:
#                 date_experience_dt = datetime.strptime(date_str_temp, '%d %B %Y')

#                 jour_experience = date_experience_dt.day
#                 mois_experience = date_experience_dt.month
#                 annee_experience = date_experience_dt.year

#                 date_experience = date_experience_dt.strftime('%Y-%m-%d')

#                 return date_experience, jour_experience, mois_experience, annee_experience

#             except ValueError as ve:
#                 print(f"Erreur de conversion de date pour l'expérience '{raw_date_experience}': {ve}")
#                 return None, None, None, None
#         return None, None, None, None
#     except Exception as e:
#         print(f"Erreur lors de l'extraction ou conversion de date_experience : {e}")
#         return None, None, None, None


import re
import logging
from datetime import datetime
from . import config # Assurez-vous d'importer config pour MOIS_MAPPING

def extract_experience_date(review_soup_article):
    """
    Extrait la date d'expérience de l'avis en utilisant des sélecteurs plus robustes.
    Tente plusieurs stratégies.
    """
    date_exp_str = None
    
    # --- Stratégie 1: Cible le paragraphe avec l'attribut data-service-review-date-of-experience-typography ---
    # Cette approche est plus robuste car elle se base sur un attribut data-* qui est moins volatile que les classes.
    try:
        # Cible directement la balise <p> avec l'attribut data-service-review-date-of-experience-typography
        # Puis, cherche la balise <span> à l'intérieur de ce <p>
        date_span_elem = review_soup_article.find('p', {'data-service-review-date-of-experience-typography': True})
        if date_span_elem:
            # Maintenant, cherchons le span à l'intérieur de ce p
            actual_date_span = date_span_elem.find('span', class_=lambda x: x and ('typography_appearance-subtle' in x or 'CDS_Typography_appearance-subtle' in x))
            if actual_date_span:
                date_exp_str = actual_date_span.get_text(strip=True)
                # logging.info(f"Date d'expérience trouvée (Stratégie 1 par data attribute) : {date_exp_str}")
                
    except Exception as e:
        logging.warning(f"Échec de la Stratégie 1 pour la date d'expérience: {e}")

    
    jour = None
    mois = None
    annee = None
    
    if date_exp_str:
        try:
            # Nettoyage et conversion de la date
            date_exp_str = date_exp_str.replace('Date de l\'expérience:', '').strip()
            
            # Utilisation de regex pour extraire jour, mois, année
            match = re.search(r'(\d{1,2})\s+([a-zA-Zàâéèêëîïôöûüùç]+)\s+(\d{4})', date_exp_str)
            if match:
                jour = int(match.group(1))
                mois_nom = match.group(2).lower()
                annee = int(match.group(3))
                
                mois_mapping = {
                    'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6,
                    'juillet': 7, 'août': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
                }
                mois = mois_mapping.get(mois_nom, None)
                
                if mois:
                    # Reformater la date au format 'AAAA-MM-JJ' pour la colonne date_experience
                    date_exp_str_formatted = f"{annee:04d}-{mois:02d}-{jour:02d}"
                    return date_exp_str_formatted, jour, mois, annee
                else:
                    logging.warning(f"Mois '{mois_nom}' non reconnu pour la date d'expérience: {date_exp_str}")
            else:
                logging.warning(f"Format de date non reconnu pour l'expérience: {date_exp_str}")
        except Exception as e:
            logging.error(f"Erreur lors du parsing de la date d'expérience '{date_exp_str}': {e}")
            date_exp_str = None # Reset en cas d'erreur de parsing
            jour = None
            mois = None
            annee = None

    logging.info(f"Retour pour date d'expérience: str={date_exp_str}, jour={jour}, mois={mois}, année={annee}")
    return date_exp_str, jour, mois, annee


# def extract_review_content(review_soup_article):
#     """
#     Extrait le contenu de l'avis. Tente d'abord le paragraphe principal,
#     puis le titre de l'avis si le paragraphe est absent.
#     Retourne le texte de l'avis/titre ou une chaîne vide si rien n'est trouvé.
#     """
#     content = "" # Initialise à une chaîne vide par défaut
#     title = "" # Initialise le titre à vide aussi

#     try:
#         # Tente d'abord d'extraire le contenu principal
#         content_div = review_soup_article.find('div', class_='styles_reviewContent__tuXiN')
#         if content_div:
#             content_p = content_div.find('p', class_='CDS_Typography_appearance-default__bedfe1 CDS_Typography_body-l__bedfe1')
#             if content_p:
#                 content = content_p.text.strip()

#         # Tente toujours d'extraire le titre, qu'il y ait du contenu principal ou non
#         # Nous l'utiliserons pour le hash si le contenu principal est vide, ou pour le combiner.
#         title_extracted = extract_review_title(review_soup_article)
#         if title_extracted:
#             title = title_extracted

#     except Exception as e:
#         logging.error(f"Erreur inattendue lors de l'extraction du contenu principal ou du titre: {e}")

#     # Retourne le contenu principal si trouvé, sinon le titre préfixé
#     # Ceci est pour le champ 'contenu' dans la DB.
#     if content:
#         return content
#     elif title:
#         return "Titre: " + title
#     return "" # Retourne vide si ni contenu ni titre

def extract_review_content(review_soup_article):
    """
    Extrait le contenu de l'avis. Tente d'abord le paragraphe principal,
    puis le titre de l'avis si le paragraphe est absent.
    Retourne le texte de l'avis/titre ou une chaîne vide si rien n'est trouvé.
    """
    content = ""
    title = ""

    try:
        content_div = review_soup_article.find('div', class_='styles_reviewContent__tuXiN')
        if content_div:
            content_p = content_div.find('p', class_='CDS_Typography_appearance-default__bedfe1 CDS_Typography_body-l__bedfe1')
            if content_p:
                content = content_p.text.strip()

        # Le titre est toujours extrait pour le fallback
        title_extracted = extract_review_title(review_soup_article)
        if title_extracted:
            title = title_extracted

    except Exception as e:
        logging.error(f"Erreur inattendue lors de l'extraction du contenu principal ou du titre dans extract_review_content: {e}")

    if content:
        return content
    elif title:
        return "Titre: " + title
    return ""

# def extract_review_title(review_soup_article):
#     """
#     Extrait le titre de l'avis en utilisant le chemin du XPath fourni.
#     XPath: article/div/section/div[2]/a/h2
#     """
#     try:
#         div1 = review_soup_article.find('div', recursive=False)
#         if div1:
#             section1 = div1.find('section', recursive=False)
#             if section1:
#                 div2 = section1.find('div', class_='styles_reviewContent__tuXiN')
#                 if div2:
#                     a_tag = div2.find('a', recursive=False)
#                     if a_tag:
#                         title_tag = a_tag.find('h2', recursive=False)
#                         if title_tag:
#                             return title_tag.text.strip()
#         return None
#     except Exception as e:
#         logging.error(f"Erreur lors de l'extraction du titre: {e}")
#         return None

def extract_review_title(review_soup_article):
    """
    Extrait le titre de l'avis.
    """
    try:
        title_tag = review_soup_article.select_one('div > section > div.styles_reviewContent__tuXiN > a > h2')
        if title_tag:
            return title_tag.text.strip()
        return None
    except Exception as e:
        # Ici l'erreur 'str.find' pourrait être levée si review_soup_article n'est pas un Tag
        logging.error(f"Erreur lors de l'extraction du titre dans extract_review_title: {e}")
        return None


# def extract_invitation_status(review_soup_article):
#     """Vérifie si l'avis est sur invitation.
#     Retourne True si l'avis est sur invitation, sinon False."""
#     try:
#         details_div = review_soup_article.find('div', class_='typography_body-m__k2UI7 typography_appearance-subtle__PYOVM styles_detailsIcon__n1OXF')
#         if details_div:
#             button_span = details_div.find('span', {'role': 'button'})
#             if button_span:
#                 invitation_span = button_span.find('span')
#                 if invitation_span and "sur invitation" in invitation_span.get_text(strip=True).lower():
#                     return True
#         return False
#     except Exception:
#         return False

def extract_invitation_status(review_soup_article):
    """
    Vérifie si l'avis est marqué "Sur invitation".
    Cible la div avec l'attribut data-name="review-label-tooltip-trigger" et vérifie le texte.
    Retourne True si l'avis est sur invitation, sinon False.
    """
    try:
        # La div avec data-name="review-label-tooltip-trigger" est la plus stable.
        invitation_label_div = review_soup_article.find('div', {'data-name': 'review-label-tooltip-trigger'})
        
        if invitation_label_div:
            # Vérifiez si le texte "Sur invitation" est présent n'importe où dans cette div ou ses enfants.
            # Convertir en minuscules pour une correspondance insensible à la casse.
            if "sur invitation" in invitation_label_div.get_text(strip=True).lower():
                return True
        return False
    except Exception as e:
        # Log l'erreur si quelque chose d'inattendu se produit, mais retourne False.
        logging.warning(f"Erreur lors de l'extraction du statut d'invitation: {e}")
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


def generate_content_hash(review_soup_article):
    """
    Génère un hash SHA256 basé sur le titre et le contenu principal de l'avis.
    Si le contenu principal est vide, le hash est basé sur le titre.
    Si ni le titre ni le contenu ne sont trouvés, retourne None.
    """
    content = ""
    title = ""

    # Extraire le contenu principal (le paragraphe)
    try:
        content_div = review_soup_article.find('div', class_='styles_reviewContent__tuXiN')
        if content_div:
            content_p = content_div.find('p', class_='CDS_Typography_appearance-default__bedfe1 CDS_Typography_body-l__bedfe1')
            if content_p:
                content = content_p.text.strip()
    except Exception as e:
        logging.warning(f"Impossible d'extraire le contenu pour le hash: {e}")

    # Extraire le titre
    title_extracted = extract_review_title(review_soup_article)
    if title_extracted:
        title = title_extracted

    # Construire la chaîne à hasher
    string_to_hash = ""
    if content:
        string_to_hash += content
    if title:
        # Ajoute le titre, séparé par un délimiteur clair, pour éviter les collisions
        # si "Contenu: 'Avis super.' Titre: 'Super avis.'" vs "Contenu: 'Super avis.' Titre: 'Avis super.'"
        if string_to_hash: # Si le contenu principal existe, ajoute le titre après
            string_to_hash += "|||" + title
        else: # Si seul le titre existe, utilise-le comme base
            string_to_hash = title

    if string_to_hash:
        return hashlib.sha256(string_to_hash.encode('utf-8')).hexdigest()
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
    
