import streamlit as st
import pandas as pd
import plotly.express as px

# 1. SETUP PAGINA (Design Premium)
st.set_page_config(page_title="Match Analysis Fisica", layout="wide", initial_sidebar_state="expanded")

# Colori sociali (Verde e Grigio scuro per il contrasto)
COLOR_1T = '#27ae60'
COLOR_2T = '#34495e'
colori_tempi = {'MATCH (1)': COLOR_1T, 'MATCH (2)': COLOR_2T}

# 2. COLLEGAMENTO AL DATABASE (GOOGLE SHEETS)
URL_FOGLIO_GOOGLE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTzh8377Fpku7ZtWpaCnTSRSiswjlwVcz8UMEDMVJTnq0KQeFXe83jfLStHQ6_4AkNIWRdQcZWXQ4xP/pub?output=csv"

@st.cache_data(ttl=300)
def carica_dati(url):
    if "INCOLLA_QUI" in url or not url.startswith("http"):
        return pd.DataFrame()
    try:
        # Leggiamo il CSV
        df = pd.read_csv(url)
        
        # Pulizia spazi nei nomi delle colonne
        df.columns = df.columns.str.strip()
        
        # Conversione dei campi numerici formattati all'italiana (es. 4.005,52 -> 4005.52)
        cols_da_convertire = [
            'Distance Total', 'Distance Per Min', 'High Speed Running (Absolute)', 
            'HSR Per Minute (Absolute)', 'Distance Zone 6 (Absolute)', 'Max Speed'
        ]
        
        for col in cols_da_convertire:
            if col in df.columns:
                # Se la colonna è di tipo testo con punti e virgole, puliamo e convertiamo
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Pulizia delle altre colonne numeriche intere
        cols_intere = ['Accelerations Z4 to Z6', 'Deceleration Z4 to Z6']
        for col in cols_intere:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        # Creazione nome completo giocatore pulito
        df['Giocatore'] = df['Player Last Name'].astype(str).str.strip() + " " + df['Player First Name'].astype(str).str.strip()
        
        # Filtriamo solo le righe delle partite
        df['Drill Title'] = df['Drill Title'].astype(str).str.strip()
        df_match = df[df['Drill Title'].isin(['MATCH (1)', 'MATCH (2)'])].copy()
                
        return df_match
    except Exception as e:
        st.error(f"Errore durante l'elaborazione dei dati: {e}")
        return pd.DataFrame()

st.title("⚽ Dashboard Performance Fisica")
st.markdown("---")

# Caricamento dei dati
with st.spinner('Sincronizzazione database in corso...'):
    df_totale = carica_dati(URL_FOGLIO_GOOGLE)

if df_totale.empty:
    st.error("⚠️ Attenzione: Impossibile leggere il Foglio Google o il file è vuoto.")
else:
    pagina = st.sidebar.radio("Navigazione", ["📊 Analisi Singola Partita", "📈 Storico Stagionale"])

    # --- PAGINA 1: SINGOLA PARTITA ---
    if pagina == "📊 Analisi Singola Partita":
        st.sidebar.markdown("### Selezione Partita")
        
        # Mostriamo tutte le date disponibili in ordine
        date_disponibili = sorted(df_totale['Session Date'].dropna().unique())
        
        if len(date_disponibili) > 0:
            # Di default selezioniamo l'ultima partita inserita (la più recente)
            data_selezionata = st.sidebar.selectbox("Scegli la data della partita:", date_disponibili, index=len(date_disponibili)-1)
            
            df_match = df_totale[df_totale['Session Date'] == data_selezionata]
            
            st.subheader(f"Report Partita del {data_selezionata}")
            
            # --- SEZIONE KPI HIGHLIGHTS ---
            st.markdown("##### 🚀 Top Performers della Partita (Totale 1T+2T)")
            col1, col2, col3 = st.columns(3)
            
            df_somma_giocatori = df_match.groupby('Giocatore').sum(numeric_only=True).reset_index()
            
            if not df_somma_giocatori.empty:
                top_dist = df_somma_giocatori.loc[df_somma_giocatori['Distance Total'].idxmax()]
                top_hsr = df_somma_giocatori.loc[df_somma_giocatori['High Speed Running (Absolute)'].idxmax()]
                
                df_max_speed = df_match.groupby('Giocatore')['Max Speed'].max().reset_index()
                top_speed = df_max_speed.loc[df_max_speed['Max Speed'].idxmax()]
                
                with col1:
                    st.metric(label="🏆 Maggior Distanza (m)", value=f"{top_dist['Distance Total']:.0f}", delta=top_dist['Giocatore'], delta_color="off")
                with col2:
                    st.metric(label="⚡ Maggior High Speed Run (m)", value=f"{top_hsr['High Speed Running (Absolute)']:.0f}", delta=top_hsr['Giocatore'], delta_color="off")
                with col3:
                    st.metric(label="🏎️ Picco di Velocità (km/h)", value=f"{top_speed['Max Speed']:.1f}", delta=top_speed['Giocatore'], delta_color="off")
                    
            st.markdown("---")
            
            # --- GRAFICI PROFESSIONALI ---
            st.markdown("### 📊 Analisi Volumi (Somma 1T + 2T)")
            
            fig_dist = px.bar(df_match, x='Giocatore', y='Distance Total', color='Drill Title', 
                         title="Distanza Totale (metri)", barmode='stack', text_auto='.0f',
                         color_discrete_map=colori_tempi, template="plotly_white")
            fig_dist.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None)
            st.plotly_chart(fig_dist, use_container_width=True)

            fig_hsr = px.bar(df_match, x='Giocatore', y='High Speed Running (Absolute)', color='Drill Title', 
                         title="Corsa ad Alta Velocità (>19.8 km/h)", barmode='stack', text_auto='.0f',
                         color_discrete_map=colori_tempi, template="plotly_white")
            fig_hsr.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None)
            st.plotly_chart(fig_hsr, use_container_width=True)

            st.markdown("### ⚡ Analisi Intensità (Confronto Diretto)")
            
            fig_speed = px.bar(df_match, x='Giocatore', y='Max Speed', color='Drill Title', 
                         title="Velocità Massima (km/h)", barmode='group', text_auto='.1f',
                         color_discrete_map=colori_tempi, template="plotly_white")
            fig_speed.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None)
            st.plotly_chart(fig_speed, use_container_width=True)
        else:
            st.warning("Nessuna data trovata nel database.")

    # --- PAGINA 2: STORICO GIOCATORE ---
    elif pagina == "📈 Storico Stagionale":
        st.sidebar.markdown("### Selezione Atleta")
        
        lista_giocatori = sorted(df_totale['Giocatore'].unique())
        if len(lista_giocatori) > 0:
            giocatore_selezionato = st.sidebar.selectbox("Seleziona il giocatore:", lista_giocatori)
            
            st.subheader(f"Andamento Stagionale: {giocatore_selezionato}")
            
            df_giocatore = df_totale[df_totale['Giocatore'] == giocatore_selezionato]
            
            aggregazioni = {'Distance Total': 'sum', 'High Speed Running (Absolute)': 'sum', 'Max Speed': 'max'}
            df_raggruppato = df_giocatore.groupby('Session Date').agg(aggregazioni).reset_index()
            
            df_raggruppato['Data Ordine'] = pd.to_datetime(df_raggruppato['Session Date'], format='%d/%m/%Y', errors='coerce')
            df_raggruppato = df_raggruppato.sort_values('Data Ordine')
            
            fig_storico = px.line(df_raggruppato, x='Session Date', y='Distance Total', markers=True, 
                          title="Andamento Distanza Totale in Partita (m)", template="plotly_white")
            fig_storico.update_traces(line_color=COLOR_1T, marker=dict(size=10, color=COLOR_2T), line_width=3)
            fig_storico.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title="Data Partita")
            st.plotly_chart(fig_storico, use_container_width=True)

            fig_storico_vel = px.line(df_raggruppato, x='Session Date', y='Max Speed', markers=True, 
                          title="Andamento Velocità Massima (km/h)", template="plotly_white")
            fig_storico_vel.update_traces(line_color='#e74c3c', marker=dict(size=10, color='#c0392b'), line_width=3)
            fig_storico_vel.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title="Data Partita")
            st.plotly_chart(fig_storico_vel, use_container_width=True)
        else:
            st.warning("Nessun giocatore trovato nel database.")
