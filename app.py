import streamlit as st
import sqlite3
import pandas as pd
import os
import time
from datetime import datetime, timedelta

DB_FILE = 'system_edms.db'

# --- FUNKCJE BAZODANOWE ---
def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn()
    with open('schema.sql', 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.close()

if not os.path.exists(DB_FILE):
    init_db()

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="EDMS Enterprise v3.0", layout="wide")

# --- SYSTEM POWIADOMIEŃ ---
if 'msg' not in st.session_state: st.session_state.msg = None
if 'msg_type' not in st.session_state: st.session_state.msg_type = "info"

def set_msg(text, type="info"):
    st.session_state.msg = text
    st.session_state.msg_type = type

# Wyświetlanie zapisanego komunikatu na górze strony
if st.session_state.msg:
    if st.session_state.msg_type == "success": st.success(st.session_state.msg)
    elif st.session_state.msg_type == "error": st.error(st.session_state.msg)
    elif st.session_state.msg_type == "warning": st.warning(st.session_state.msg)
    st.session_state.msg = None

# Zarządzanie sesją użytkownika
if 'user' not in st.session_state:
    st.session_state.user = None

def logout():
    st.session_state.user = None
    set_msg("Wylogowano pomyślnie.", "info")
    st.rerun()

# --- EKRAN LOGOWANIA I REJESTRACJI ---
if st.session_state.user is None:
    tab1, tab2 = st.tabs(["🔐 Logowanie", "📝 Rejestracja Nowego Pracownika"])
    
    with tab1:
        st.subheader("Panel Logowania")
        email = st.text_input("Adres Email", key="login_email")
        password = st.text_input("Hasło", type="password", key="login_pass")
        if st.button("ZALOGUJ"):
            if not email or not password:
                st.error("Błąd: Proszę wpisać email i hasło.")
            else:
                with get_conn() as conn:
                    res = pd.read_sql("SELECT * FROM Pracownicy WHERE email=? AND haslo=?", conn, params=(email, password))
                    if not res.empty:
                        st.session_state.user = res.iloc[0].to_dict()
                        set_msg(f"Witaj z powrotem, {st.session_state.user['imie']}!", "success")
                        st.rerun()
                    else:
                        st.error("Błąd: Nieprawidłowe dane logowania.")
    
    with tab2:
        st.subheader("Formularz Rejestracji")
        with st.form("reg_form", clear_on_submit=True):
            r_name = st.text_input("Imię")
            r_surname = st.text_input("Nazwisko")
            r_email = st.text_input("Email (Login)")
            r_pass = st.text_input("Hasło", type="password")
            with get_conn() as conn:
                depts = pd.read_sql("SELECT id_departamentu, nazwa_dept FROM Departamenty", conn)
            r_dept = st.selectbox("Dział", depts['nazwa_dept'].tolist())
            
            if st.form_submit_button("STWÓRZ KONTO"):
                if not r_name or not r_surname or not r_email or not r_pass:
                    st.error("Walidacja: Wszystkie pola muszą być wypełnione!")
                elif "@" not in r_email:
                    st.error("Walidacja: Podany email jest nieprawidłowy.")
                else:
                    d_id = depts[depts['nazwa_dept'] == r_dept]['id_departamentu'].values[0]
                    try:
                        with get_conn() as conn:
                            conn.execute("INSERT INTO Pracownicy (imie, nazwisko, email, haslo, rola, id_departamentu) VALUES (?, ?, ?, ?, 'USER', ?)", 
                                         (r_name, r_surname, r_email, r_pass, int(d_id)))
                            conn.commit()
                        st.success("Sukces! Konto zostało utworzone. Możesz teraz przejść do logowania.")
                    except:
                        st.error("Błąd: Ten email jest już zajęty.")
    st.stop()

# --- GŁÓWNA APLIKACJA ---
u = st.session_state.user
st.sidebar.title("🏢 EDMS System")
st.sidebar.write(f"Zalogowany: **{u['imie']} {u['nazwisko']}**")

if u['rola'] == 'ADMIN':
    menu = ["Pulpit Zarządczy", "Zasoby i Naprawy", "Wszystkie Rezerwacje"]
else:
    menu = ["Pulpit Zarządczy", "Nowa Rezerwacja", "Moje Rezerwacje", "Wymiana Biurek", "Zgłoś Usterkę"]

choice = st.sidebar.radio("NAWIGACJA", menu)
if st.sidebar.button("WYLOGUJ"): logout()

# --- 1. PULPIT ZARZĄDCZY ---
if choice == "Pulpit Zarządczy":
    st.header("Analiza obłożenia budynków")
    with get_conn() as conn:
        df = pd.read_sql("SELECT * FROM VW_RAPORT_OBLOZENIA", conn)
        df['% ZAJĘCIA'] = (df['ZAREZERWOWANE_DZIS'] / df['WSZYSTKIE_BIURKA'] * 100).round(2)
        st.table(df)

# --- 2. NOWA REZERWACJA ---
elif choice == "Nowa Rezerwacja":
    st.header("Zarezerwuj biurko (Walidacja czasu)")
    with get_conn() as conn:
        buds = pd.read_sql("SELECT nazwa FROM Budynki", conn)['nazwa'].tolist()
        wybrany_bud = st.selectbox("Budynek", buds)
        
        biurka = pd.read_sql("""
            SELECT b.id_biurka, b.kod_biurka || ' (' || b.strefa || ')' as opis
            FROM Biurka b JOIN Pietra p ON b.id_pietra = p.id_pietra
            JOIN Budynki bud ON p.id_budynku = bud.id_budynku
            WHERE bud.nazwa = ? AND b.czy_sprawne = 1
        """, conn, params=(wybrany_bud,))
        
        if biurka.empty:
            st.warning("Brak dostępnych biurek.")
        else:
            wybrane_b = st.selectbox("Wybierz biurko", biurka['opis'].tolist())
            b_id = biurka[biurka['opis'] == wybrane_b]['id_biurka'].values[0]
            
            c1, c2, c3 = st.columns(3)
            d_rez = c1.date_input("Dzień", min_value=datetime.now(), max_value=datetime.now()+timedelta(days=7))
            h_start = c2.selectbox("Godzina rozpoczęcia", list(range(7, 21)))
            h_end = c3.selectbox("Godzina zakończenia", list(range(h_start+1, 22)))
            
            if st.button("POTWIERDŹ REZERWACJĘ"):
                with get_conn() as conn_tr:
                    cur = conn_tr.cursor()
                    try:
                        cur.execute("BEGIN TRANSACTION")
                        check = cur.execute("SELECT COUNT(*) FROM Rezerwacje WHERE id_biurka=? AND data_rezerwacji=? AND (godzina_start < ? AND godzina_koniec > ?)", (int(b_id), str(d_rez), h_end, h_start)).fetchone()[0]
                        if check > 0:
                            st.error("Błąd: To biurko jest już zarezerwowane w tych godzinach!")
                        else:
                            cur.execute("INSERT INTO Rezerwacje (id_pracownika, id_biurka, data_rezerwacji, godzina_start, godzina_koniec, id_statusu) VALUES (?, ?, ?, ?, ?, 1)",
                                       (u['id_pracownika'], int(b_id), str(d_rez), h_start, h_end))
                            conn_tr.commit()
                            set_msg(f"Pomyślnie zarezerwowano biurko {wybrane_b}!", "success")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Błąd bazy danych: {e}")

# --- 3. MOJE REZERWACJE ---
elif choice == "Moje Rezerwacje":
    st.header("Twoja lista rezerwacji")
    with get_conn() as conn:
        df = pd.read_sql("""
            SELECT b.kod_biurka, b.strefa, r.data_rezerwacji, 
                   r.godzina_start || ':00 - ' || r.godzina_koniec || ':00' as czas
            FROM Rezerwacje r JOIN Biurka b ON r.id_biurka = b.id_biurka
            WHERE r.id_pracownika = ? ORDER BY r.data_rezerwacji ASC
        """, conn, params=(u['id_pracownika'],))
        if df.empty: st.info("Brak aktywnych rezerwacji.")
        else: st.table(df)

# --- 4. WYMIANA BIUREK ---
elif choice == "Wymiana Biurek":
    st.header("System wymiany rezerwacji")
    t1, t2 = st.tabs(["Wyślij ofertę", "Otrzymane prośby"])
    with t1:
        with get_conn() as conn:
            my = pd.read_sql("SELECT r.id_rezerwacji, b.kod_biurka || ' (' || r.data_rezerwacji || ')' as opis FROM Rezerwacje r JOIN Biurka b ON r.id_biurka = b.id_biurka WHERE r.id_pracownika=?", conn, params=(u['id_pracownika'],))
            others = pd.read_sql("SELECT r.id_rezerwacji, p.nazwisko || ': ' || b.kod_biurka || ' (' || r.data_rezerwacji || ')' as opis, p.id_pracownika FROM Rezerwacje r JOIN Pracownicy p ON r.id_pracownika = p.id_pracownika JOIN Biurka b ON r.id_biurka = b.id_biurka WHERE r.id_pracownika != ?", conn, params=(u['id_pracownika'],))
            
            if not my.empty and not others.empty:
                moje = st.selectbox("Twoje biurko", my['opis'].tolist())
                m_id = my[my['opis'] == moje]['id_rezerwacji'].values[0]
                ich = st.selectbox("Z kim się zamienić?", others['opis'].tolist())
                o_row = others[others['opis'] == ich].iloc[0]
                if st.button("WYŚLIJ PROŚBĘ"):
                    conn.execute("INSERT INTO Zamiany (id_nadawcy, id_odbiorcy, id_rez_nadawcy, id_rez_odbiorcy) VALUES (?, ?, ?, ?)", (u['id_pracownika'], int(o_row['id_pracownika']), int(m_id), int(o_row['id_rezerwacji'])))
                    conn.commit()
                    set_msg("Prośba o wymianę została wysłana.", "success")
                    st.rerun()

    with t2:
        with get_conn() as conn:
            prośby = pd.read_sql("SELECT z.id_zamiany, p.imie || ' ' || p.nazwisko as od, b1.kod_biurka as prop, b2.kod_biurka as twoje, z.id_rez_nadawcy, z.id_rez_odbiorcy, z.id_nadawcy FROM Zamiany z JOIN Pracownicy p ON z.id_nadawcy = p.id_pracownika JOIN Rezerwacje r1 ON z.id_rez_nadawcy = r1.id_rezerwacji JOIN Biurka b1 ON r1.id_biurka = b1.id_biurka JOIN Rezerwacje r2 ON z.id_rez_odbiorcy = r2.id_rezerwacji JOIN Biurka b2 ON r2.id_biurka = b2.id_biurka WHERE z.id_odbiorcy = ? AND z.status = 'OCZEKUJACE'", conn, params=(u['id_pracownika'],))
            for _, r in prośby.iterrows():
                st.info(f"Wymiana od {r['od']}: Jego {r['prop']} za Twoje {r['twoje']}")
                c1, c2 = st.columns(2)
                if c1.button(f"AKCEPTUJ #{r['id_zamiany']}"):
                    cur = conn.cursor()
                    try:
                        cur.execute("BEGIN TRANSACTION")
                        cur.execute("UPDATE Rezerwacje SET id_pracownika = ? WHERE id_rezerwacji = ?", (u['id_pracownika'], r['id_rez_nadawcy']))
                        cur.execute("UPDATE Rezerwacje SET id_pracownika = ? WHERE id_rezerwacji = ?", (r['id_nadawcy'], r['id_rez_odbiorcy']))
                        cur.execute("UPDATE Zamiany SET status = 'ZAAKCEPTOWANE' WHERE id_zamiany = ?", (r['id_zamiany'],))
                        conn.commit()
                        set_msg("Sukces! Biurka zostały zamienione.", "success")
                        st.rerun()
                    except: conn.rollback(); st.error("Błąd transakcji.")
                if c2.button(f"ODRZUĆ #{r['id_zamiany']}"):
                    conn.execute("UPDATE Zamiany SET status = 'ODRZUCONE' WHERE id_zamiany = ?", (r['id_zamiany'],))
                    conn.commit(); set_msg("Prośba odrzucona.", "warning"); st.rerun()

# --- 5. ZGŁOŚ USTERKĘ ---
elif choice == "Zgłoś Usterkę":
    st.header("Zgłoś problem techniczny")
    with get_conn() as conn:
        biurka = pd.read_sql("SELECT id_biurka, kod_biurka || ' - ' || strefa as opis FROM Biurka WHERE czy_sprawne = 1", conn)
        target = st.selectbox("Wybierz biurko", biurka['opis'].tolist())
        target_id = biurka[biurka['opis'] == target]['id_biurka'].values[0]
        opis = st.text_area("Opis awarii")
        if st.button("WYŚLIJ RAPORT"):
            if not opis: st.error("Proszę wpisać opis usterki!")
            else:
                conn.execute("INSERT INTO Usterki (id_biurka, opis) VALUES (?, ?)", (int(target_id), opis))
                conn.commit()
                set_msg(f"Usterka zgłoszona. Biurko {target} wyłączone z rezerwacji.", "warning")
                st.rerun()

# --- 6. ADMIN: ZASOBY I NAPRAWY ---
elif choice == "Zasoby i Naprawy":
    st.header("Panel Administratora - Infrastruktura")
    with get_conn() as conn:
        df_desks = pd.read_sql("SELECT id_biurka, kod_biurka, strefa, czy_sprawne FROM Biurka", conn)
        st.dataframe(df_desks)
        
        broken = df_desks[df_desks['czy_sprawne'] == 0]
        if not broken.empty:
            target = st.selectbox("Biurko do naprawy", broken['kod_biurka'].tolist())
            if st.button("OZNACZ JAKO NAPRAWIONE"):
                conn.execute("UPDATE Biurka SET czy_sprawne = 1 WHERE kod_biurka = ?", (target,))
                conn.commit()
                set_msg(f"BIURKO {target} PRZYWRÓCONE DO UŻYTKU!", "success")
                st.rerun()
        else: st.success("Wszystkie zasoby są sprawne.")

# --- 7. ADMIN: WSZYSTKIE REZERWACJE ---
elif choice == "Wszystkie Rezerwacje":
    st.header("Moderacja bazy rezerwacji")
    with get_conn() as conn:
        df = pd.read_sql("SELECT r.id_rezerwacji, p.nazwisko, b.kod_biurka, r.data_rezerwacji FROM Rezerwacje r JOIN Pracownicy p ON r.id_pracownika = p.id_pracownika JOIN Biurka b ON r.id_biurka = b.id_biurka", conn)
        st.table(df)
        id_del = st.number_input("ID rezerwacji do usunięcia", step=1)
        if st.button("USUŃ DEFINITYWNIE"):
            with get_conn() as conn_del:
                cur_del = conn_del.cursor()
                try:
                    cur_del.execute("BEGIN TRANSACTION")
                    cur_del.execute("DELETE FROM Zamiany WHERE id_rez_nadawcy = ? OR id_rez_odbiorcy = ?", (int(id_del), int(id_del)))
                    cur_del.execute("DELETE FROM Rezerwacje WHERE id_rezerwacji = ?", (int(id_del),))
                    conn_del.commit()
                    set_msg(f"Rezerwacja nr {id_del} została usunięta.", "success")
                    st.rerun()
                except Exception as e: st.error(f"Błąd: {e}")