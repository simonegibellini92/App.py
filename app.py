import streamlit as st
import pandas as pd
import plotly.express as px

# 1. SETUP PAGINA
st.set_page_config(page_title="Match Analysis Fisica", layout="wide", initial_sidebar_state="expanded")

COLOR_1T = '#27ae60'
COLOR_2T = '#34495e'
colori_tempi = {'1° Tempo': COLOR_1T, '2° Tempo': COLOR_2T}

# Configurazione Plotly ottimizzata per mobile: niente drag accidentale, scrolling fluido e solo tasto download
PLOTLY_CONFIG = {
    'displayModeBar': True,
    'modeBarButtonsToRemove': [
        'zoom2d', 'pan2d', 'select2d', 'lasso2d', 
        'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d',
        'orbitController', 'tableRotation'
    ],
    'displaylogo': False,
    'toImageButtonOptions': {
        'format': 'png',
        'filename': 'prestazione_atleta',
        'scale': 2
    }
}

URL_FOGLIO_GOOGLE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTzh8377Fpku7ZtWpaCnTSRSiswjlwVcz8UMEDMVJTnq0KQeFXe83jfLStHQ6_4AkNIWRdQcZWXQ4xP/pub?output=csv"

# Pulsante di ricarica rapida nella barra laterale
if st.sidebar.button("🔄 Aggiorna Dati"):
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
            if col not in ['Custom Player Id', 'Player First Name', 'Player Last Name', 'Player Position', 'Session Date', 'Drill Title', 'Settimana', 'Tipo Sessione', 'Data Pulita']:
                df[col] = df[col].apply(clean_italian_number)

        if 'Session Date' in df.columns:
            df['Session Date'] = df['Session Date'].astype(str).str.strip()

        if 'Player Last Name' in df.columns and 'Player First Name' in df.columns:
            df['Player Last Name'] = df['Player Last Name'].fillna('').astype(str).str.strip()
            df['Player First Name'] = df['Player First Name'].fillna('').astype(str).str.strip()
            df['Giocatore'] = df['Player Last Name'] + " " + df['Player First Name']
        else:
            df['Giocatore'] = "Atleta Sconosciuto"
            
        df = df[df['Giocatore'] != " "]

        if 'Drill Title' in df.columns:
            df['Drill Upper'] = df['Drill Title'].astype(str).str.upper()
            df_match = df[df['Drill Upper'].str.contains('MATCH|PARTITA|1|2', na=False)].copy()
            
            def etichetta_tempo(titolo):
                if '1' in titolo or 'FIRST' in titolo:
                    return '1° Tempo'
                elif '2' in titolo or 'SECOND' in titolo:
                    return '2° Tempo'
                return titolo
            df_match['Drill Title'] = df_match['Drill Upper'].apply(etichetta_tempo)
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
            
            col_distanza = 'Distance Total' if 'Distance Total' in df_match.columns else None
            col_hsr = 'High Speed Running' if 'High Speed Running' in df_match.columns else None
            col_speed = 'Max Speed' if 'Max Speed' in df_match.columns else None
            col_acc = 'Acceleration Z4 to Z6' if 'Acceleration Z4 to Z6' in df_match.columns else None
            col_dec = 'Deceleration Z4 to Z6' if 'Deceleration Z4 to Z6' in df_match.columns else None
            col_zone6 = 'Distance Zone 6' if 'Distance Zone 6' in df_match.columns else None
            col_dist_min = 'Distance Per Minute' if 'Distance Per Minute' in df_match.columns else None
            col_hsr_min = 'HSR Per Minute' if 'HSR Per Minute' in df_match.columns else None
            
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
                fig_dist.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None, dragmode=False)
                st.plotly_chart(fig_dist, use_container_width=True, config=PLOTLY_CONFIG)

            if col_hsr:
                fig_hsr = px.bar(df_match, x='Giocatore', y=col_hsr, color='Drill Title', 
                             title="Corsa ad Alta Velocità (HSR)", barmode='stack', text_auto='.0f',
                             color_discrete_map=colori_tempi, template="plotly_white")
                fig_hsr.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None, dragmode=False)
                st.plotly_chart(fig_hsr, use_container_width=True, config=PLOTLY_CONFIG)

            # --- INTENSITÀ E METRICHE AL MINUTO ---
            st.markdown("### ⚡ Intensità e Metriche al Minuto")
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                if col_speed:
                    fig_speed = px.bar(df_match, x='Giocatore', y=col_speed, color='Drill Title', 
                                 title="Velocità Massima (km/h)", barmode='group', text_auto='.1f',
                                 color_discrete_map=colori_tempi, template="plotly_white")
                    fig_speed.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None, dragmode=False)
                    st.plotly_chart(fig_speed, use_container_width=True, config=PLOTLY_CONFIG)
                if col_dist_min:
                    fig_dmin = px.bar(df_match, x='Giocatore', y=col_dist_min, color='Drill Title', 
                                 title="Distanza al Minuto (m/min)", barmode='group', text_auto='.1f',
                                 color_discrete_map=colori_tempi, template="plotly_white")
                    fig_dmin.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None, dragmode=False)
                    st.plotly_chart(fig_dmin, use_container_width=True, config=PLOTLY_CONFIG)
                    
            with col_g2:
                if col_zone6:
                    fig_z6 = px.bar(df_match, x='Giocatore', y=col_zone6, color='Drill Title', 
                                 title="Distanza Zona 6 (Sprint)", barmode='stack', text_auto='.0f',
                                 color_discrete_map=colori_tempi, template="plotly_white")
                    fig_z6.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None, dragmode=False)
                    st.plotly_chart(fig_z6, use_container_width=True, config=PLOTLY_CONFIG)
                if col_hsr_min:
                    fig_hmin = px.bar(df_match, x='Giocatore', y=col_hsr_min, color='Drill Title', 
                                 title="HSR al Minuto", barmode='group', text_auto='.2f',
                                 color_discrete_map=colori_tempi, template="plotly_white")
                    fig_hmin.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None, dragmode=False)
                    st.plotly_chart(fig_hmin, use_container_width=True, config=PLOTLY_CONFIG)

            # Accelerazioni e Decelerazioni
            if col_acc or col_dec:
                st.markdown("### 🔄 Accelerazioni e Decelerazioni")
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    if col_acc:
                        fig_acc = px.bar(df_match, x='Giocatore', y=col_acc, color='Drill Title', 
                                     title="Accelerazioni (Z4 to Z6)", barmode='stack', text_auto='.0f',
                                     color_discrete_map=colori_tempi, template="plotly_white")
                        fig_acc.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None, dragmode=False)
                        st.plotly_chart(fig_acc, use_container_width=True, config=PLOTLY_CONFIG)
                with col_a2:
                    if col_dec:
                        fig_dec = px.bar(df_match, x='Giocatore', y=col_dec, color='Drill Title', 
                                     title="Decelerazioni (Z4 to Z6)", barmode='stack', text_auto='.0f',
                                     color_discrete_map=colori_tempi, template="plotly_white")
                        fig_dec.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None, dragmode=False)
                        st.plotly_chart(fig_dec, use_container_width=True, config=PLOTLY_CONFIG)
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
            
            col_distanza = 'Distance Total' if 'Distance Total' in df_giocatore.columns else None
            col_hsr = 'High Speed Running' if 'High Speed Running' in df_giocatore.columns else None
            col_speed = 'Max Speed' if 'Max Speed' in df_giocatore.columns else None
            col_acc = 'Acceleration Z4 to Z6' if 'Acceleration Z4 to Z6' in df_giocatore.columns else None
            col_dec = 'Deceleration Z4 to Z6' if 'Deceleration Z4 to Z6' in df_giocatore.columns else None
            col_zone6 = 'Distance Zone 6' if 'Distance Zone 6' in df_giocatore.columns else None
            col_dist_min = 'Distance Per Minute' if 'Distance Per Minute' in df_giocatore.columns else None
            col_hsr_min = 'HSR Per Minute' if 'HSR Per Minute' in df_giocatore.columns else None

            # Calcolo dei Record / Migliore Prestazione Stagionale in Partita
            df_match_player = df_giocatore.groupby('Session Date').agg({
                col_distanza: 'sum' if col_distanza else 'first',
                col_hsr: 'sum' if col_hsr else 'first',
                col_speed: 'max' if col_speed else 'first'
            }).reset_index()

            st.markdown("##### 🌟 Migliore Prestazione Stagionale")
            bc1, bc2, bc3 = st.columns(3)
            
            if not df_match_player.empty:
                if col_distanza:
                    best_dist = df_match_player.loc[df_match_player[col_distanza].idxmax()]
                    with bc1:
                        st.metric(label="🏆 Record Distanza", value=f"{best_dist[col_distanza]:.0f} m", delta=f"Data: {best_dist['Session Date']}", delta_color="off")
                if col_hsr:
                    best_hsr = df_match_player.loc[df_match_player[col_hsr].idxmax()]
                    with bc2:
                        st.metric(label="⚡ Record HSR", value=f"{best_hsr[col_hsr]:.0f} m", delta=f"Data: {best_hsr['Session Date']}", delta_color="off")
                if col_speed:
                    best_spd = df_match_player.loc[df_match_player[col_speed].idxmax()]
                    with bc3:
                        st.metric(label="🏎️ Record Velocità Max", value=f"{best_spd[col_speed]:.1f} km/h", delta=f"Data: {best_spd['Session Date']}", delta_color="off")

            st.markdown("---")
            
            # Aggregazioni per i grafici temporali
            aggregazioni = {}
            if col_distanza: aggregazioni[col_distanza] = 'sum'
            if col_hsr: aggregazioni[col_hsr] = 'sum'
            if col_speed: aggregazioni[col_speed] = 'max'
            if col_acc: aggregazioni[col_acc] = 'sum'
            if col_dec: aggregazioni[col_dec] = 'sum'
            if col_zone6: aggregazioni[col_zone6] = 'sum'
            if col_dist_min: aggregazioni[col_dist_min] = 'mean'
            if col_hsr_min: aggregazioni[col_hsr_min] = 'mean'
            
            df_raggruppato = df_giocatore.groupby('Session Date').agg(aggregazioni).reset_index()
            df_raggruppato['Data Ordine'] = pd.to_datetime(df_raggruppato['Session Date'], format='%d/%m/%Y', errors='coerce')
            df_raggruppato = df_raggruppato.sort_values('Data Ordine')
            
            # Grafici Storici Completi
            if col_distanza:
                fig_storico = px.line(df_raggruppato, x='Session Date', y=col_distanza, markers=True, 
                              title="Andamento Distanza Totale in Partita (m)", template="plotly_white")
                fig_storico.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title="Data Partita", dragmode=False)
                st.plotly_chart(fig_storico, use_container_width=True, config=PLOTLY_CONFIG)

            if col_hsr:
                fig_storico_hsr = px.line(df_raggruppato, x='Session Date', y=col_hsr, markers=True, 
                              title="Andamento High Speed Running (m)", template="plotly_white")
                fig_storico_hsr.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title="Data Partita", dragmode=False)
                st.plotly_chart(fig_storico_hsr, use_container_width=True, config=PLOTLY_CONFIG)

            if col_speed:
                fig_storico_vel = px.line(df_raggruppato, x='Session Date', y=col_speed, markers=True, 
                              title="Andamento Velocità Massima (km/h)", template="plotly_white")
                fig_storico_vel.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title="Data Partita", dragmode=False)
                st.plotly_chart(fig_storico_vel, use_container_width=True, config=PLOTLY_CONFIG)

            if col_zone6:
                fig_storico_z6 = px.line(df_raggruppato, x='Session Date', y=col_zone6, markers=True, 
                              title="Andamento Distanza Zona 6 (Sprint)", template="plotly_white")
                fig_storico_z6.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title="Data Partita", dragmode=False)
                st.plotly_chart(fig_storico_z6, use_container_width=True, config=PLOTLY_CONFIG)

            if col_dist_min:
                fig_storico_dmin = px.line(df_raggruppato, x='Session Date', y=col_dist_min, markers=True, 
                              title="Andamento Distanza al Minuto (m/min)", template="plotly_white")
                fig_storico_dmin.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title="Data Partita", dragmode=False)
                st.plotly_chart(fig_storico_dmin, use_container_width=True, config=PLOTLY_CONFIG)

            if col_acc:
                fig_storico_acc = px.line(df_raggruppato, x='Session Date', y=col_acc, markers=True, 
                              title="Andamento Accelerazioni", template="plotly_white")
                fig_storico_acc.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title="Data Partita", dragmode=False)
                st.plotly_chart(fig_storico_acc, use_container_width=True, config=PLOTLY_CONFIG)

            if col_dec:
                fig_storico_dec = px.line(df_raggruppato, x='Session Date', y=col_dec, markers=True, 
                              title="Andamento Decelerazioni", template="plotly_white")
                fig_storico_dec.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title="Data Partita", dragmode=False)
                st.plotly_chart(fig_storico_dec, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            st.warning("Nessun giocatore trovato nel database.")
