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
        df = pd.read_csv(url)
        
        # Pulizia rigorosa dei nomi delle colonne da spazi multipli o invisibili
        df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
        
        # Funzione di pulizia numeri italiani (es. 4.005,52 -> 4005.52)
        def clean_italian_number(val):
            if pd.isna(val):
                return 0.0
            if isinstance(val, (int, float)):
                return float(val)
            val_str = str(val).strip()
            if val_str == '' or val_str.lower() == 'nan':
                return 0.0
            val_str = val_str.replace('.', '').replace(',', '.')
            try:
                return float(val_str)
            except:
                return 0.0

        # Convertiamo tutte le colonne numeriche in automatico
        for col in df.columns:
            if col not in ['Player First Name', 'Player Last Name', 'Player Position', 'Session Date', 'Drill Title', 'Giocatore']:
                df[col] = df[col].apply(clean_italian_number)

        # Creazione nome giocatore unendo nome e cognome
        if 'Player Last Name' in df.columns and 'Player First Name' in df.columns:
            df['Giocatore'] = df['Player Last Name'].astype(str).str.strip() + " " + df['Player First Name'].astype(str).str.strip()
        else:
            df['Giocatore'] = "Atleta"

        # Filtriamo solo le righe delle partite
        if 'Drill Title' in df.columns:
            df['Drill Title'] = df['Drill Title'].astype(str).str.strip()
            df_match = df[df['Drill Title'].isin(['MATCH (1)', 'MATCH (2)'])].copy()
        else:
            df_match = df.copy()
                
        return df_match
    except Exception as e:
        st.error(f"Errore durante l'elaborazione dei dati: {e}")
        return pd.DataFrame()

st.title("⚽ Dashboard Performance Fisica")
st.markdown("---")

with st.spinner('Sincronizzazione database in corso...'):
    df_totale = carica_dati(URL_FOGLIO_GOOGLE)

if df_totale.empty:
    st.error("⚠️ Attenzione: Impossibile leggere il Foglio Google o il file è vuoto.")
else:
    pagina = st.sidebar.radio("Navigazione", ["📊 Analisi Singola Partita", "📈 Storico Stagionale"])

    # --- PAGINA 1: SINGOLA PARTITA ---
    if pagina == "📊 Analisi Singola Partita":
        st.sidebar.markdown("### Selezione Partita")
        
        date_disponibili = sorted(df_totale['Session Date'].dropna().unique()) if 'Session Date' in df_totale.columns else []
        
        if len(date_disponibili) > 0:
            data_selezionata = st.sidebar.selectbox("Scegli la data della partita:", date_disponibili, index=len(date_disponibili)-1)
            df_match = df_totale[df_totale['Session Date'] == data_selezionata]
            
            st.subheader(f"Report Partita del {data_selezionata}")
            
            # Ricerca automatica delle colonne chiave nel dataframe
            col_distanza = next((c for c in df_match.columns if 'distance total' in c.lower() or 'distanza' in c.lower()), None)
            col_hsr = next((c for c in df_match.columns if 'high speed' in c.lower() or 'hsr' in c.lower()), None)
            col_speed = next((c for c in df_match.columns if 'max speed' in c.lower() or 'velocità' in c.lower()), None)
            
            # --- SEZIONE KPI HIGHLIGHTS ---
            st.markdown("##### 🚀 Top Performers della Partita (Totale 1T+2T)")
            col1, col2, col3 = st.columns(3)
            
            if col_distanza and col_hsr and col_speed:
                df_somma_giocatori = df_match.groupby('Giocatore')[[col_distanza, col_hsr]].sum().reset_index()
                top_dist = df_somma_giocatori.loc[df_somma_giocatori[col_distanza].idxmax()]
                top_hsr = df_somma_giocatori.loc[df_somma_giocatori[col_hsr].idxmax()]
                
                df_max_speed = df_match.groupby('Giocatore')[col_speed].max().reset_index()
                top_speed = df_max_speed.loc[df_max_speed[col_speed].idxmax()]
                
                with col1:
                    st.metric(label="🏆 Maggior Distanza (m)", value=f"{top_dist[col_distanza]:.0f}", delta=top_dist['Giocatore'], delta_color="off")
                with col2:
                    st.metric(label="⚡ Maggior High Speed Run (m)", value=f"{top_hsr[col_hsr]:.0f}", delta=top_hsr['Giocatore'], delta_color="off")
                with col3:
                    st.metric(label="🏎️ Picco di Velocità (km/h)", value=f"{top_speed[col_speed]:.1f}", delta=top_speed['Giocatore'], delta_color="off")
            else:
                st.info("Verifica i nomi delle colonne nel file.")
                    
            st.markdown("---")
            
            # --- GRAFICI PROFESSIONALI ---
            if col_distanza:
                st.markdown("### 📊 Analisi Volumi (Somma 1T + 2T)")
                fig_dist = px.bar(df_match, x='Giocatore', y=col_distanza, color='Drill Title', 
                             title="Distanza Totale (metri)", barmode='stack', text_auto='.0f',
                             color_discrete_map=colori_tempi, template="plotly_white")
                fig_dist.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None)
                st.plotly_chart(fig_dist, use_container_width=True)

            if col_hsr:
                fig_hsr = px.bar(df_match, x='Giocatore', y=col_hsr, color='Drill Title', 
                             title="Corsa ad Alta Velocità", barmode='stack', text_auto='.0f',
                             color_discrete_map=colori_tempi, template="plotly_white")
                fig_hsr.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None)
                st.plotly_chart(fig_hsr, use_container_width=True)

            if col_speed:
                st.markdown("### ⚡ Analisi Intensità (Confronto Diretto)")
                fig_speed = px.bar(df_match, x='Giocatore', y=col_speed, color='Drill Title', 
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
            
            col_distanza = next((c for c in df_totale.columns if 'distance total' in c.lower() or 'distanza' in c.lower()), None)
            col_speed = next((c for c in df_totale.columns if 'max speed' in c.lower() or 'velocità' in c.lower()), None)
            
            aggregazioni = {}
            if col_distanza: aggregazioni[col_distanza] = 'sum'
            if col_speed: aggregazioni[col_speed] = 'max'
            
            df_raggruppato = df_giocatore.groupby('Session Date').agg(aggregazioni).reset_index()
            
            df_raggruppato['Data Ordine'] = pd.to_datetime(df_raggruppato['Session Date'], format='%d/%m/%Y', errors='coerce')
            df_raggruppato = df_raggruppato.sort_values('Data Ordine')
            
            if col_distanza:
                fig_storico = px.line(df_raggruppato, x='Session Date', y=col_distanza, markers=True, 
                              title="Andamento Distanza Totale in Partita (m)", template="plotly_white")
                fig_storico.update_traces(line_color=COLOR_1T, marker=dict(size=10, color=COLOR_2T), line_width=3)
                fig_storico.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title="Data Partita")
                st.plotly_chart(fig_storico, use_container_width=True)

            if col_speed:
                fig_storico_vel = px.line(df_raggruppato, x='Session Date', y=col_speed, markers=True, 
                              title="Andamento Velocità Massima (km/h)", template="plotly_white")
                fig_storico_vel.update_traces(line_color='#e74c3c', marker=dict(size=10, color='#c0392b'), line_width=3)
                fig_storico_vel.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title="Data Partita")
                st.plotly_chart(fig_storico_vel, use_container_width=True)
        else:
            st.warning("Nessun giocatore trovato nel database.")
