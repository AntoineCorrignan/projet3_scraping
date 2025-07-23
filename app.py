# app.py
import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import pytz # Pour gérer les fuseaux horaires si vos dates sont en UTC dans la DB

# --- Configuration de la page Streamlit ---
st.set_page_config(
    page_title="Dashboard Avis Nickel",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Configuration de la connexion à la base de données Neon ---
@st.cache_resource
def init_connection():
    # Accès aux secrets comme précédemment discuté, avec double indexation
    db_config = st.secrets["connections"]["postgresql"]
    return psycopg2.connect(**db_config)

conn = init_connection()

# --- Fonction pour charger les données (avec mise en cache) ---
# Le TTL peut être ajusté en fonction de la fréquence de mise à jour des données
@st.cache_data(ttl=600) # Mise en cache des données pendant 10 minutes
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        return pd.DataFrame(rows, columns=colnames)

# --- Fonctions utilitaires pour les calculs (si besoin) ---
def format_timedelta(td):
    """Formate un timedelta en HH:MM"""
    if pd.isna(td):
        return "N/A"
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}"

# --- Barre latérale pour les filtres ---
st.sidebar.header("Filtres")

# Date de début et de fin pour les données des graphiques
today = datetime.now()
start_date_default = today - timedelta(days=90) # Les 3 derniers mois par défaut
end_date_default = today

date_range = st.sidebar.date_input(
    "Sélectionnez la période pour les graphiques :",
    value=(start_date_default, end_date_default),
    max_value=today
)

if len(date_range) == 2:
    start_date_filter = datetime.combine(date_range[0], datetime.min.time())
    end_date_filter = datetime.combine(date_range[1], datetime.max.time())
else:
    # Si l'utilisateur n'a sélectionné qu'une seule date, utilisez la comme début et fin
    start_date_filter = datetime.combine(date_range[0], datetime.min.time())
    end_date_filter = datetime.combine(date_range[0], datetime.max.time())

# Déterminer la semaine actuelle pour les KPIs (du lundi au dimanche)
# Assurez-vous que le fuseau horaire correspond à celui de votre base de données si nécessaire
# Pour l'exemple, nous allons travailler avec l'heure locale ou UTC si la DB est UTC
# Si vos dates de DB sont UTC, il est bon de convertir les dates Python en UTC pour la comparaison
tz = pytz.timezone("Europe/Paris") # Ou le fuseau horaire de votre DB si elle est cohérente
now_tz = tz.localize(datetime.now())

# Début de la semaine (lundi)
start_of_week = now_tz - timedelta(days=now_tz.weekday())
start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

# Fin de la semaine (dimanche)
end_of_week = start_of_week + timedelta(days=6)
end_of_week = end_of_week.replace(hour=23, minute=59, second=59, microsecond=999999)

# --- Titre du Dashboard ---
st.title("📊 Dashboard des Avis Nickel")
st.markdown("Ce tableau de bord présente une analyse des avis clients collectés pour Nickel.")

# --- Section des KPIs (Key Performance Indicators) ---
st.header("Indicateurs Clés de Performance (KPIs)")

col1, col2, col3, col4 = st.columns(4)

# KPI 1: Nombre d'avis reçus cette semaine
query_kpi_avis_semaine = f"""
SELECT COUNT(id)
FROM reviews_nickel
WHERE date_publication >= '{start_of_week.isoformat()}' AND date_publication <= '{end_of_week.isoformat()}';
"""
df_avis_semaine = run_query(query_kpi_avis_semaine)
nombre_avis_semaine = df_avis_semaine.iloc[0, 0] if not df_avis_semaine.empty else 0
col1.metric("Avis reçus cette semaine", nombre_avis_semaine)

# KPI 2: Pourcentage d'avis répondus
# Pourcentage d'avis sur la période filtrée par le date_range
query_kpi_reponse = f"""
SELECT
    COUNT(CASE WHEN reponse = TRUE THEN 1 END) AS count_responded,
    COUNT(id) AS total_reviews
FROM reviews_nickel
WHERE date_publication >= '{start_date_filter.isoformat()}' AND date_publication <= '{end_date_filter.isoformat()}';
"""
df_reponse = run_query(query_kpi_reponse)
pourcentage_reponse = 0
if not df_reponse.empty and df_reponse.iloc[0]['total_reviews'] > 0:
    pourcentage_reponse = (df_reponse.iloc[0]['count_responded'] / df_reponse.iloc[0]['total_reviews']) * 100
col2.metric("% Avis répondus", f"{pourcentage_reponse:.1f}%")

# KPI 3: Temps de réponse moyen en HH:MM (sur la période filtrée par le date_range)
query_kpi_temps_reponse = f"""
SELECT AVG(EXTRACT(EPOCH FROM (date_reponse - date_publication))) AS avg_response_seconds
FROM reviews_nickel
WHERE reponse = TRUE
  AND date_publication >= '{start_date_filter.isoformat()}' AND date_publication <= '{end_date_filter.isoformat()}';
"""
df_temps_reponse = run_query(query_kpi_temps_reponse)
temps_moyen_secondes = df_temps_reponse.iloc[0, 0] if not df_temps_reponse.empty and df_temps_reponse.iloc[0, 0] is not None else 0
temps_moyen_td = timedelta(seconds=float(temps_moyen_secondes))
col3.metric("Temps de réponse moyen", format_timedelta(temps_moyen_td))

# KPI 4: Note moyenne sur la semaine en cours
query_kpi_note_semaine = f"""
SELECT AVG(note_avis)
FROM reviews_nickel
WHERE date_publication >= '{start_of_week.isoformat()}' AND date_publication <= '{end_of_week.isoformat()}';
"""
df_note_semaine = run_query(query_kpi_note_semaine)
note_moyenne_semaine = df_note_semaine.iloc[0, 0] if not df_note_semaine.empty and df_note_semaine.iloc[0, 0] is not None else 0
col4.metric("Note moyenne cette semaine", f"{note_moyenne_semaine:.2f}/5")

# --- Section des Graphiques d'Évolution ---
st.header("Évolution des indicateurs")

# Requête principale pour les graphiques (agrégation journalière)
query_evolution = f"""
SELECT
    DATE_TRUNC('day', date_publication) AS date_jour,
    AVG(note_avis) AS note_moyenne,
    COUNT(id) AS nombre_avis,
    COUNT(CASE WHEN avis_sur_invitation = TRUE THEN 1 END) AS avis_invitation_count,
    COUNT(id) AS total_avis_jour,
    AVG(CASE WHEN avis_sur_invitation = TRUE THEN note_avis END) AS note_moyenne_invitation
FROM reviews_nickel
WHERE date_publication >= '{start_date_filter.isoformat()}' AND date_publication <= '{end_date_filter.isoformat()}'
GROUP BY date_jour
ORDER BY date_jour;
"""
df_evolution = run_query(query_evolution)

# Calcul du pourcentage d'avis sur invitation
if not df_evolution.empty:
    df_evolution['pourcentage_invitation'] = (df_evolution['avis_invitation_count'] / df_evolution['total_avis_jour']) * 100
    df_evolution = df_evolution.sort_values('date_jour')
    df_evolution['date_jour'] = df_evolution['date_jour'].dt.date # Simplifie l'affichage de la date

# Graphique 1: Évolution de la note moyenne
st.subheader("Évolution de la Note Moyenne")
if not df_evolution.empty:
    fig_note = px.line(df_evolution, x='date_jour', y='note_moyenne',
                       title='Note Moyenne des Avis au fil du temps',
                       labels={'date_jour': 'Date', 'note_moyenne': 'Note Moyenne'})
    fig_note.update_traces(mode='lines+markers')
    st.plotly_chart(fig_note, use_container_width=True)
else:
    st.info("Pas de données disponibles pour l'évolution de la note moyenne sur la période sélectionnée.")

# Graphique 2: Évolution du nombre d'avis
st.subheader("Évolution du Nombre d'Avis")
if not df_evolution.empty:
    fig_count = px.line(df_evolution, x='date_jour', y='nombre_avis',
                        title='Nombre Total d\'Avis au fil du temps',
                        labels={'date_jour': 'Date', 'nombre_avis': 'Nombre d\'Avis'})
    fig_count.update_traces(mode='lines+markers')
    st.plotly_chart(fig_count, use_container_width=True)
else:
    st.info("Pas de données disponibles pour l'évolution du nombre d'avis sur la période sélectionnée.")

# Graphique 3: Pourcentage d'avis sur invitation
st.subheader("Pourcentage d'Avis sur Invitation")
if not df_evolution.empty:
    fig_pct_invit = px.line(df_evolution, x='date_jour', y='pourcentage_invitation',
                           title='Pourcentage d\'Avis provenant d\'Invitations',
                           labels={'date_jour': 'Date', 'pourcentage_invitation': '% sur Invitation'})
    fig_pct_invit.update_traces(mode='lines+markers')
    st.plotly_chart(fig_pct_invit, use_container_width=True)
else:
    st.info("Pas de données disponibles pour le pourcentage d'avis sur invitation sur la période sélectionnée.")

# Graphique 4: Note moyenne des avis sur invitation
st.subheader("Note Moyenne des Avis sur Invitation")
if not df_evolution.empty:
    fig_note_invit = px.line(df_evolution, x='date_jour', y='note_moyenne_invitation',
                            title='Note Moyenne des Avis sur Invitation',
                            labels={'date_jour': 'Date', 'note_moyenne_invitation': 'Note Moyenne (Invitation)'})
    fig_note_invit.update_traces(mode='lines+markers')
    st.plotly_chart(fig_note_invit, use_container_width=True)
else:
    st.info("Pas de données disponibles pour la note moyenne des avis sur invitation sur la période sélectionnée.")

st.markdown("---")
st.caption("Données mises à jour toutes les 10 minutes.")