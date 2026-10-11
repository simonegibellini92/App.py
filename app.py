import streamlit as st
import pandas as pd
import plotly.express as px

# 1. SETUP PAGINA
st.set_page_config(page_title="Match Analysis Fisica", layout="wide", initial_sidebar_state="expanded")

COLOR_1T = '#27ae60'
COLOR_2T = '#34495e'
colori_tempi = {'MATCH (1)': COLOR_1T, 'MATCH (2)': COLOR_2T}

URL_FOGLIO_GOOGLE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTzh8377Fpku7ZtWpaCnTSRSiswjlwVcz8UMEDMVJTnq0KQeFXe83jfLStHQ6_4AkNIWRdQcZWXQ4xP/pub?output=csv"

if st.sidebar.button("🔄 Ricarica Dati da Google Sheets"):
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=300)
def carica_dati(url):
    if "INCOLLA_QUI" in url or not url.startswith("http"):
        return pd.DataFrame()
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
        
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

        for col in df.columns:
            if col not in ['Player First Name', 'Player Last Name', 'Player Position', 'Session Date', 'Drill Title', 'Giocatore']:
                df[col] = df[col].apply(clean_italian_number)

        # Pulizia date
        if 'Session Date' in df.columns:
            df['Session Date'] = df['Session Date'].astype(str).str.strip()

        # Creazione nome giocatore
        if 'Player Last Name' in df.columns and 'Player First Name' in df.columns:
            df['Player Last Name'] = df['Player Last Name'].fillna('').astype(str).str.strip()
            df['Player First Name'] = df['Player First Name'].fillna('').astype(str).str.strip()
            df['Giocatore'] = df['Player Last Name'] + " " + df['Player First Name']
        else:
            df['Giocatore'] = "Atleta Sconosciuto"
            
        df = df[df['Giocatore'] != " "]

        # Filtro flessibile tempi
        if 'Drill Title' in df.columns:
            df['Drill Clean'] = df['Drill Title'].astype(str).str.upper().str.replace(r'[^A-Z0-9]', '', regex=True)
            df_match = df[df['Drill Clean'].isin(['MATCH1', 'MATCH2', 'MATCH (1)', 'MATCH (2)'])].copy()
            df_match['Drill Title'] = df_match['Drill Clean'].apply(lambda x: 'MATCH (1)' if '1' in x else 'MATCH (2)')
        else:
            df_match = df.copy()
                
        return df_match
    except Exception as e:
        st.error(f"Errore di lettura: {e}")
        return pd.DataFrame()

st.title("⚽ Dashboard Performance Fisica")
st.markdown("---")

with st.spinner('Sincronizzazione in corso...'):
    df_totale = carica_dati(URL_FOGLIO_GOOGLE)

# --- PANNELLO DI DEBUG (TI MOSTRA COSA LEGGE PYTHON) ---
with st.expander("🔍 Debug Avanzato (Clicca per aprire)", expanded=False):
    st.write(f"📊 Righe totali caricate: {len(df_totale)}")
    st.write(f"📋 Colonne rilevate nel file: {list(df_totale.columns)}")
    if not df_totale.empty:
        st.write(f"📅 Date uniche trovate: {df_totale['Session Date'].unique() if 'Session Date' in df_totale.columns else 'Colonna mancante'}")
        st.write(f"👥 Giocatori unici trovati: {df_totale['Giocatore'].unique() if 'Giocatore' in df_totale.columns else 'Colonna mancante'}")

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
            
            df_match = df_totale[df_totale['Session Date'] == data_selezionata].copy()
            
            st.subheader(f"Report Partita del {data_selezionata}")
            
            # Ricerca flessibile di TUTTE le colonne chiave
            col_distanza = next((c for c in df_match.columns if 'distance total' in c.lower() or 'distanza' in c.lower()), None)
            col_hsr = next((c for c in df_match.columns if 'high speed' in c.lower() or 'hsr' in c.lower() and 'min' not in c.lower()), None)
            col_speed = next((c for c in df_match.columns if 'max speed' in c.lower() or 'velocità' in c.lower()), None)
            col_acc = next((c for c in df_match.columns if 'accelerations' in c.lower() or 'accelerazioni' in c.lower()), None)
            col_dec = next((c for c in df_match.columns if 'deceleration' in c.lower() or 'decelerazioni' in c.lower()), None)
            col_zone6 = next((c for c in df_match.columns if 'zone 6' in c.lower() or 'z6' in c.lower()), None)
            col_dist_min = next((c for c in df_match.columns if 'distance per min' in c.lower() or 'distanza al minuto' in c.lower()), None)
            col_hsr_min = next((c for c in df_match.columns if 'hsr per min' in c.lower() or 'hsr al minuto' in c.lower()), None)
            
            # --- SEZIONE KPI HIGHLIGHTS ---
            st.markdown("##### 🚀 Top Performers della Partita (Totale 1T+2T)")
            c1, c2, c3 = st.columns(3)
            
            if col_distanza and col_hsr and col_speed:
                df_somma_giocatori = df_match.groupby('Giocatore')[[col_distanza, col_hsr]].sum().reset_index()
                top_dist = df_somma_giocatori.loc[df_somma_giocatori[col_distanza].idxmax()]
                top_hsr = df_somma_giocatori.loc[df_somma_giocatori[col_hsr].idxmax()]
                
                df_max_speed = df_match.groupby('Giocatore')[col_speed].max().reset_index()
                top_speed = df_max_speed.loc[df_max_speed[col_speed].idxmax()]
                
                with c1:
                    st.metric(label="🏆 Maggior Distanza (m)", value=f"{top_dist[col_distanza]:.0f}", delta=top_dist['Giocatore'], delta_color="off")
                with c2:
                    st.metric(label="⚡ High Speed Run (m)", value=f"{top_hsr[col_hsr]:.0f}", delta=top_hsr['Giocatore'], delta_color="off")
                with c3:
                    st.metric(label="🏎️ Picco di Velocità (km/h)", value=f"{top_speed[col_speed]:.1f}", delta=top_speed['Giocatore'], delta_color="off")
                    
            st.markdown("---")
            
            # --- GRAFICI DI VOLUME ---
            if col_distanza:
                st.markdown("### 📊 Volumi di Lavoro")
                fig_dist = px.bar(df_match, x='Giocatore', y=col_distanza, color='Drill Title', 
                             title="Distanza Totale (metri)", barmode='stack', text_auto='.0f',
                             color_discrete_map=colori_tempi, template="plotly_white")
                fig_dist.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None)
                st.plotly_chart(fig_dist, use_container_width=True)

            if col_hsr:
                fig_hsr = px.bar(df_match, x='Giocatore', y=col_hsr, color='Drill Title', 
                             title="Corsa ad Alta Velocità (HSR)", barmode='stack', text_auto='.0f',
                             color_discrete_map=colori_tempi, template="plotly_white")
                fig_hsr.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None)
                st.plotly_chart(fig_hsr, use_container_width=True)

            # --- INTENSITÀ E METRICHE AL MINUTO ---
            st.markdown("### ⚡ Intensità e Metriche al Minuto")
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                if col_speed:
                    fig_speed = px.bar(df_match, x='Giocatore', y=col_speed, color='Drill Title', 
                                 title="Velocità Massima (km/h)", barmode='group', text_auto='.1f',
                                 color_discrete_map=colori_tempi, template="plotly_white")
                    fig_speed.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None)
                    st.plotly_chart(fig_speed, use_container_width=True)
                if col_dist_min:
                    fig_dmin = px.bar(df_match, x='Giocatore', y=col_dist_min, color='Drill Title', 
                                 title="Distanza al Minuto (m/min)", barmode='group', text_auto='.1f',
                                 color_discrete_map=colori_tempi, template="plotly_white")
                    fig_dmin.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None)
                    st.plotly_chart(fig_dmin, use_container_width=True)
                    
            with col_g2:
                if col_zone6:
                    fig_z6 = px.bar(df_match, x='Giocatore', y=col_zone6, color='Drill Title', 
                                 title="Distanza Zona 6 (Sprint)", barmode='stack', text_auto='.0f',
                                 color_discrete_map=colori_tempi, template="plotly_white")
                    fig_z6.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None)
                    st.plotly_chart(fig_z6, use_container_width=True)
                if col_hsr_min:
                    fig_hmin = px.bar(df_match, x='Giocatore', y=col_hsr_min, color='Drill Title', 
                                 title="HSR al Minuto", barmode='group', text_auto='.2f',
                                 color_discrete_map=colori_tempi, template="plotly_white")
                    fig_hmin.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None)
                    st.plotly_chart(fig_hmin, use_container_width=True)

            # Accelerazioni e Decelerazioni
            if col_acc or col_dec:
                st.markdown("### 🔄 Accelerazioni e Decelerazioni")
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    if col_acc:
                        fig_acc = px.bar(df_match, x='Giocatore', y=col_acc, color='Drill Title', 
                                     title="Accelerazioni (Z4 to Z6)", barmode='stack', text_auto='.0f',
                                     color_discrete_map=colori_tempi, template="plotly_white")
                        fig_acc.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None)
                        st.plotly_chart(fig_acc, use_container_width=True)
                with col_a2:
                    if col_dec:
                        fig_dec = px.bar(df_match, x='Giocatore', y=col_dec, color='Drill Title', 
                                     title="Decelerazioni (Z4 to Z6)", barmode='stack', text_auto='.0f',
                                     color_discrete_map=colori_tempi, template="plotly_white")
                        fig_dec.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None)
                        st.plotly_chart(fig_dec, use_container_width=True)
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
            col_hsr = next((c for c in df_totale.columns if 'high speed' in c.lower() or 'hsr' in c.lower() and 'min' not in c.lower()), None)
            
            aggregazioni = {}
            if col_distanza: aggregazioni[col_distanza] = 'sum'
            if col_hsr: aggregazioni[col_hsr] = 'sum'
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

            if col_hsr:
                fig_storico_hsr = px.line(df_raggruppato, x='Session Date', y=col_hsr, markers=True, 
                              title="Andamento High Speed Running (m)", template="plotly_white")
                fig_storico_hsr.update_traces(line_color='#2980b9', marker=dict(size=10, color='#1abc9c'), line_width=3)
                fig_storico_hsr.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title="Data Partita")
                st.plotly_chart(fig_storico_hsr, use_container_width=True)

            if col_speed:
                fig_storico_vel = px.line(df_raggruppato, x='Session Date', y=col_speed, markers=True, 
                              title="Andamento Velocità Massima (km/h)", template="plotly_white")
                fig_storico_vel.update_traces(line_color='#e74c3c', marker=dict(size=10, color='#c0392b'), line_width=3)
                fig_storico_vel.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title="Data Partita")
                st.plotly_chart(fig_storico_vel, use_container_width=True)
        else:
            st.warning("Nessun giocatore trovato nel database.")
