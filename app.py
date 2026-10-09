import streamlit as st
import pandas as pd
import plotly.express as px

# Configurazione della pagina
st.set_page_config(page_title="Match Analysis Fisica", layout="wide")

st.title("⚽ Report Fisico Calcio")

# Menu laterale
pagina = st.sidebar.radio("Seleziona Pagina", ["Singola Partita", "Storico Giocatore"])

# Colori per i grafici
colori_tempi = {'MATCH (1)': '#27ae60', 'MATCH (2)': '#7f8c8d'} # Verde e Grigio

# --- PAGINA 1: SINGOLA PARTITA ---
if pagina == "Singola Partita":
    st.header("Analisi Singola Partita (1° vs 2° Tempo)")
    
    file_caricato = st.file_uploader("Carica il file CSV della sessione", type=['csv'])
    
    if file_caricato is not None:
        df = pd.read_csv(file_caricato)
        df['Giocatore'] = df['Player Last Name'] + " " + df['Player First Name']
        df_match = df[df['Drill Title'].isin(['MATCH (1)', 'MATCH (2)'])]
        
        parametri_volume = [
            'Distance Total', 'High Speed Running (Absolute)', 
            'Distance Zone 6 (Absolute)', 'Accelerations Z4 to Z6', 'Deceleration Z4 to Z6'
        ]
        parametri_intensita = [
            'Distance Per Min', 'HSR Per Minute (Absolute)', 'Max Speed'
        ]
        
        st.subheader("📊 Parametri di Volume (1° e 2° tempo sommati)")
        for param in parametri_volume:
            fig = px.bar(df_match, x='Giocatore', y=param, color='Drill Title', 
                         title=f"{param}", barmode='stack',
                         color_discrete_map=colori_tempi)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("⚡ Parametri di Intensità (Confronto diretto)")
        for param in parametri_intensita:
            fig = px.bar(df_match, x='Giocatore', y=param, color='Drill Title', 
                         title=f"{param}", barmode='group',
                         color_discrete_map=colori_tempi)
            st.plotly_chart(fig, use_container_width=True)

# --- PAGINA 2: STORICO GIOCATORE ---
elif pagina == "Storico Giocatore":
    st.header("📈 Storico Stagionale Giocatore")
    st.info("Carica qui tutti i CSV delle partite passate per vedere l'andamento.")
    
    files_caricati = st.file_uploader("Carica i CSV", type=['csv'], accept_multiple_files=True)
    
    if files_caricati:
        dataframes = []
        for file in files_caricati:
            df_temp = pd.read_csv(file)
            dataframes.append(df_temp)
            
        df_storico = pd.concat(dataframes)
        df_storico['Giocatore'] = df_storico['Player Last Name'] + " " + df_storico['Player First Name']
        
        # Filtriamo solo le righe della partita
        df_storico = df_storico[df_storico['Drill Title'].isin(['MATCH (1)', 'MATCH (2)'])]
        
        # Seleziona il giocatore
        lista_giocatori = sorted(df_storico['Giocatore'].unique())
        giocatore_selezionato = st.selectbox("Seleziona Giocatore", lista_giocatori)
        
        # Filtra i dati per il giocatore scelto
        df_giocatore = df_storico[df_storico['Giocatore'] == giocatore_selezionato]
        
        # Definiamo come aggregare i dati (Somma per i volumi, Massimo per Max Speed, Media per i valori al minuto)
        aggregazioni = {
            'Distance Total': 'sum',
            'High Speed Running (Absolute)': 'sum',
            'Distance Zone 6 (Absolute)': 'sum',
            'Accelerations Z4 to Z6': 'sum',
            'Deceleration Z4 to Z6': 'sum',
            'Max Speed': 'max',
            'Distance Per Min': 'mean'
        }
        
        # Raggruppiamo per Data
        df_raggruppato = df_giocatore.groupby('Session Date').agg(aggregazioni).reset_index()
        
        # Ordiniamo per data (nel caso i file siano caricati in disordine)
        df_raggruppato['Session Date'] = pd.to_datetime(df_raggruppato['Session Date'], format='%d/%m/%Y')
        df_raggruppato = df_raggruppato.sort_values('Session Date')
        df_raggruppato['Data Formattata'] = df_raggruppato['Session Date'].dt.strftime('%d/%m/%Y')
        
        st.subheader(f"Analisi Volumi Totali per {giocatore_selezionato}")
        for param in ['Distance Total', 'High Speed Running (Absolute)', 'Distance Zone 6 (Absolute)', 'Accelerations Z4 to Z6']:
            fig = px.line(df_raggruppato, x='Data Formattata', y=param, markers=True, 
                          title=f"Andamento {param}",
                          line_shape='linear')
            fig.update_traces(line_color='#27ae60', marker_color='#2c3e50')
            st.plotly_chart(fig, use_container_width=True)
            
        st.subheader("Analisi Picchi di Intensità (Valore Max in partita)")
        fig_speed = px.line(df_raggruppato, x='Data Formattata', y='Max Speed', markers=True, 
                            title="Andamento Velocità Massima", line_shape='linear')
        fig_speed.update_traces(line_color='#e74c3c', marker_color='#2c3e50') # Usiamo il rosso per la velocità max
        st.plotly_chart(fig_speed, use_container_width=True)
