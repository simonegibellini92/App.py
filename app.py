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
# Incolla qui tra le virgolette il link generato da Google Sheets (Pubblica sul web -> CSV)
URL_FOGLIO_GOOGLE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTzh8377Fpku7ZtWpaCnTSRSiswjlwVcz8UMEDMVJTnq0KQeFXe83jfLStHQ6_4AkNIWRdQcZWXQ4xP/pub?output=csv"

# Questa funzione scarica i dati da Google. 
# st.cache_data fa in modo che l'app sia fulminea e ricarichi i dati da Google solo ogni 5 minuti (ttl=300)
@st.cache_data(ttl=300)
def carica_dati(url):
    try:
        df = pd.read_csv(url)
        # Creiamo il nome completo
        df['Giocatore'] = df['Player Last Name'] + " " + df['Player First Name']
        # Teniamo solo le righe delle partite
        df_match = df[df['Drill Title'].isin(['MATCH (1)', 'MATCH (2)'])]
        return df_match
    except Exception as e:
        return pd.DataFrame() # Ritorna un dataframe vuoto in caso di errore

st.title("⚽ Dashboard Performance Fisica")
st.markdown("---") # Linea di separazione elegante

# Caricamento dei dati "dietro le quinte"
with st.spinner('Sincronizzazione database in corso...'):
    df_totale = carica_dati(URL_FOGLIO_GOOGLE)

if df_totale.empty:
    st.error("⚠️ Attenzione: Impossibile leggere il Foglio Google. Verifica di aver incollato il link corretto e di aver scelto l'opzione '.csv'.")
else:
    pagina = st.sidebar.radio("Navigazione", ["📊 Analisi Singola Partita", "📈 Storico Stagionale"])

    # --- PAGINA 1: SINGOLA PARTITA ---
    if pagina == "📊 Analisi Singola Partita":
        st.sidebar.markdown("### Selezione Partita")
        
        # Invece del file, ora facciamo scegliere la DATA della partita!
        date_disponibili = df_totale['Session Date'].unique()
        data_selezionata = st.sidebar.selectbox("Scegli la data della partita:", date_disponibili)
        
        # Filtriamo i dati solo per la data scelta
        df_match = df_totale[df_totale['Session Date'] == data_selezionata]
        
        st.subheader(f"Report Partita del {data_selezionata}")
        
        # --- SEZIONE KPI HIGHLIGHTS (Stile cruscotto premium) ---
        st.markdown("##### 🚀 Top Performers della Partita (Totale 1T+2T)")
        col1, col2, col3 = st.columns(3)
        
        # Calcoliamo i top performers di quella data
        df_somma_giocatori = df_match.groupby('Giocatore').sum(numeric_only=True).reset_index()
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
        
        # --- GRAFICI PROFESSIONALI (Senza sfondo e minimal) ---
        st.markdown("### 📊 Analisi Volumi (Somma 1T + 2T)")
        
        # Grafico Distanza
        fig_dist = px.bar(df_match, x='Giocatore', y='Distance Total', color='Drill Title', 
                     title="Distanza Totale (metri)", barmode='stack', text_auto='.0f',
                     color_discrete_map=colori_tempi, template="plotly_white")
        fig_dist.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None)
        st.plotly_chart(fig_dist, use_container_width=True)

        # Grafico Alta Velocità
        fig_hsr = px.bar(df_match, x='Giocatore', y='High Speed Running (Absolute)', color='Drill Title', 
                     title="Corsa ad Alta Velocità (>19.8 km/h)", barmode='stack', text_auto='.0f',
                     color_discrete_map=colori_tempi, template="plotly_white")
        fig_hsr.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None)
        st.plotly_chart(fig_hsr, use_container_width=True)

        st.markdown("### ⚡ Analisi Intensità (Confronto Diretto)")
        
        # Grafico Velocità Massima
        fig_speed = px.bar(df_match, x='Giocatore', y='Max Speed', color='Drill Title', 
                     title="Velocità Massima (km/h)", barmode='group', text_auto='.1f',
                     color_discrete_map=colori_tempi, template="plotly_white")
        fig_speed.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title=None)
        st.plotly_chart(fig_speed, use_container_width=True)

    # --- PAGINA 2: STORICO GIOCATORE ---
    elif pagina == "📈 Storico Stagionale":
        st.sidebar.markdown("### Selezione Atleta")
        
        lista_giocatori = sorted(df_totale['Giocatore'].unique())
        giocatore_selezionato = st.sidebar.selectbox("Seleziona il giocatore:", lista_giocatori)
        
        st.subheader(f"Andamento Stagionale: {giocatore_selezionato}")
        
        # Filtriamo i dati per il giocatore scelto
        df_giocatore = df_totale[df_totale['Giocatore'] == giocatore_selezionato]
        
        # Aggreghiamo i dati per data (somma per volumi, massimo per la velocità)
        aggregazioni = {'Distance Total': 'sum', 'High Speed Running (Absolute)': 'sum', 'Max Speed': 'max'}
        df_raggruppato = df_giocatore.groupby('Session Date').agg(aggregazioni).reset_index()
        
        # Ordiniamo le date in modo corretto
        df_raggruppato['Data Ordine'] = pd.to_datetime(df_raggruppato['Session Date'], format='%d/%m/%Y')
        df_raggruppato = df_raggruppato.sort_values('Data Ordine')
        
        # Grafico Storico Distanza (Linea Premium)
        fig_storico = px.line(df_raggruppato, x='Session Date', y='Distance Total', markers=True, 
                      title="Andamento Distanza Totale in Partita (m)", template="plotly_white")
        fig_storico.update_traces(line_color=COLOR_1T, marker=dict(size=10, color=COLOR_2T), line_width=3)
        fig_storico.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title="Data Partita")
        st.plotly_chart(fig_storico, use_container_width=True)

        # Grafico Storico Velocità Massima
        fig_storico_vel = px.line(df_raggruppato, x='Session Date', y='Max Speed', markers=True, 
                      title="Andamento Velocità Massima (km/h)", template="plotly_white")
        fig_storico_vel.update_traces(line_color='#e74c3c', marker=dict(size=10, color='#c0392b'), line_width=3) # Rosso per la velocità
        fig_storico_vel.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_title=None, xaxis_title="Data Partita")
        st.plotly_chart(fig_storico_vel, use_container_width=True)
