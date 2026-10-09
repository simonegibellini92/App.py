import streamlit as st
import pandas as pd
import plotly.express as px

# Configurazione della pagina per adattarsi agli smartphone
st.set_page_config(page_title="Match Analysis Fisica", layout="wide")

st.title("⚽ Report Fisico Calcio")

# Menu laterale per la navigazione
pagina = st.sidebar.radio("Seleziona Pagina", ["Singola Partita", "Storico Giocatore"])

# --- PAGINA 1: SINGOLA PARTITA ---
if pagina == "Singola Partita":
    st.header("Analisi Singola Partita (1° vs 2° Tempo)")
    
    # Caricamento del file CSV
    file_caricato = st.file_uploader("Carica il file CSV della sessione", type=['csv'])
    
    if file_caricato is not None:
        # Lettura dati
        df = pd.read_csv(file_caricato)
        
        # Creiamo un nome completo per i giocatori
        df['Giocatore'] = df['Player Last Name'] + " " + df['Player First Name']
        
        # Filtriamo solo le righe che riguardano i tempi della partita
        df_match = df[df['Drill Title'].isin(['MATCH (1)', 'MATCH (2)'])]
        
        # Lista dei parametri (escludendo tempo totale e dati anagrafici)
        parametri_volume = [
            'Distance Total', 'High Speed Running (Absolute)', 
            'Distance Zone 6 (Absolute)', 'Accelerations Z4 to Z6', 'Deceleration Z4 to Z6'
        ]
        parametri_intensita = [
            'Distance Per Min', 'HSR Per Minute (Absolute)', 'Max Speed'
        ]
        
        st.subheader("📊 Parametri di Volume (Sommabili)")
        st.markdown("I grafici a **colonne impilate** mostrano il lavoro del 1° e 2° tempo sommati.")
        
        for param in parametri_volume:
            fig = px.bar(df_match, x='Giocatore', y=param, color='Drill Title', 
                         title=f"Confronto {param}", barmode='stack',
                         color_discrete_map={'MATCH (1)': '#1f77b4', 'MATCH (2)': '#ff7f0e'})
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("⚡ Parametri di Intensità (Non Sommabili)")
        st.markdown("I grafici a **colonne affiancate** confrontano le intensità e i picchi.")
        
        for param in parametri_intensita:
            fig = px.bar(df_match, x='Giocatore', y=param, color='Drill Title', 
                         title=f"Confronto {param}", barmode='group',
                         color_discrete_map={'MATCH (1)': '#1f77b4', 'MATCH (2)': '#ff7f0e'})
            st.plotly_chart(fig, use_container_width=True)

# --- PAGINA 2: STORICO GIOCATORE ---
elif pagina == "Storico Giocatore":
    st.header("📈 Storico Stagionale Giocatore")
    st.info("Per un utilizzo semplice: carica qui tutti i file CSV delle partite precedenti contemporaneamente.")
    
    files_caricati = st.file_uploader("Carica i CSV delle partite", type=['csv'], accept_multiple_files=True)
    
    if files_caricati:
        dataframes = []
        for file in files_caricati:
            df_temp = pd.read_csv(file)
            dataframes.append(df_temp)
            
        df_storico = pd.concat(dataframes)
        df_storico['Giocatore'] = df_storico['Player Last Name'] + " " + df_storico['Player First Name']
        
        # Seleziona il giocatore
        lista_giocatori = df_storico['Giocatore'].unique()
        giocatore_selezionato = st.selectbox("Seleziona Giocatore", lista_giocatori)
        
        # Filtriamo i dati per il giocatore e per il totale partita
        # Nota: per lo storico potremmo voler sommare 1T e 2T per i volumi
        st.write(f"Storico in fase di costruzione per {giocatore_selezionato}...")
        # Qui si possono implementare i grafici a linee nel passaggio successivo
