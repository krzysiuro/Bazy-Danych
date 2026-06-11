import streamlit as st
import oracledb
import pandas as pd

# CONFIG połączenia Krzysia
conn_params = {
    "user": "TWOJ_USER",
    "password": "TWOJE_HASLO",
    "dsn": "HOST:PORT/SERVICE_NAME"
}

def get_conn():
    return oracledb.connect(**conn_params)

st.title("🏢 EDMS - System Rezerwacji Biurek")

tab1, tab2, tab3 = st.tabs(["Dashboard", "Rezerwacja", "HR Panel"])

with tab1:
    st.header("Analityka obłożenia")
    with get_conn() as conn:
        df = pd.read_sql("SELECT * FROM VW_ANALIZA_OBLOZENIA", conn)
        st.dataframe(df)
        st.bar_chart(df.set_index('BUDYNEK')['PROC_OBLOZENIA'])

with tab2:
    st.header("Złóż rezerwację (Transakcja)")
    e_id = st.number_input("ID Pracownika", step=1)
    b_id = st.number_input("ID Biurka", step=1)
    d_rez = st.date_input("Data")
    
    if st.button("Rezerwuj"):
        try:
            with get_conn() as conn:
                cur = conn.cursor()
                cur.callproc("P_ZAREZERWUJ_BIURKO_TRANS", [e_id, b_id, d_rez])
                st.success("Zarezerwowano pomyślnie!")
        except Exception as e:
            st.error(f"Błąd transakcji: {e}")

with tab3:
    st.header("Dodaj Pracownika (CRUD)")
    with st.form("hr_form"):
        imie = st.text_input("Imię")
        nazw = st.text_input("Nazwisko")
        eml = st.text_input("Email")
        dep = st.number_input("ID Dept", step=1)
        if st.form_submit_button("Dodaj"):
            with get_conn() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO Pracownicy (imie, nazwisko, email, id_departamentu) VALUES (:1, :2, :3, :4)",
                            [imie, nazw, eml, dep])
                conn.commit()
                st.success("Dodano!")