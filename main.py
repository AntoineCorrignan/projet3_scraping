# main.py
from modules.scraper import run_scraper # Importe la fonction principale du module scraper

if __name__ == "__main__":
    print("Démarrage du processus de scraping...\n")
    
    # Appelle la fonction principale du scraper et stocke son retour
    #scraping_report = run_scraper(max_pages_to_scrape=3)
    scraping_report = run_scraper()
    
    # Affiche le rapport de scraping
    print("\n" + "="*50)
    print("RAPPORT DE SCRAPING")
    print("="*50)
    print(scraping_report)
    print("="*50)