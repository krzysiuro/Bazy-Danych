import sqlite3
import random
from faker import Faker
from datetime import datetime, timedelta

# Konfiguracja
fake = Faker('pl_PL')
DB_FILE = 'system_edms.db'

N_BUDYNKI = 10          
N_DEPT = 8              
N_PIETRA = 30           
N_PRACOWNICY = 150      
N_BIURKA = 300          
N_WYPOSAZENIE = 400     
N_REZERWACJE = 1000     
N_USTERKI = 50          
N_LOGI = 800           
N_ZAMIANY = 100         

def generate_intelligent_data():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    print("🚀 Rozpoczynam generowanie danych dla Twojego schematu SQL...")

    try:
        # 1. SŁOWNIKI
        print("Słowniki...")
        cursor.execute("INSERT OR IGNORE INTO S_Typy_Biurek (nazwa) VALUES ('Hot-desk'), ('Dedykowane')")
        cursor.execute("INSERT OR IGNORE INTO S_Statusy_Rezerwacji (nazwa) VALUES ('PLANOWANA'), ('ANULOWANA')")
        cursor.execute("INSERT OR IGNORE INTO S_Statusy_Usterki (nazwa) VALUES ('NOWE'), ('W NAPRAWIE')")

        # 2. BUDYNKI
        print(f"Budynki ({N_BUDYNKI})...")
        for _ in range(N_BUDYNKI):
            cursor.execute("INSERT INTO Budynki (nazwa, adres) VALUES (?, ?)", 
                           (f"Biurowiec {fake.city()} {random.choice(['Center', 'Tower', 'Park'])}", fake.street_address()))

        # 3. DEPARTAMENTY
        print(f"Departamenty ({N_DEPT})...")
        depty = ['IT', 'HR', 'Finanse', 'Legal', 'Marketing', 'Sales', 'Logistyka', 'R&D']
        for d in depty:
            cursor.execute("INSERT INTO Departamenty (nazwa_dept) VALUES (?)", (d,))

        # 4. PIĘTRA
        print(f"Piętra ({N_PIETRA})...")
        for _ in range(N_PIETRA):
            cursor.execute("INSERT INTO Pietra (id_budynku, numer_pietra) VALUES (?, ?)", 
                           (random.randint(1, N_BUDYNKI), random.randint(0, 10)))

        # 5. PRACOWNICY
        print(f"Pracownicy ({N_PRACOWNICY})...")
        for i in range(N_PRACOWNICY):
            f_name = fake.first_name()
            l_name = fake.last_name()
            email = f"user_{i}_{fake.free_email()}"
            cursor.execute("INSERT INTO Pracownicy (imie, nazwisko, email, haslo, rola, id_departamentu) VALUES (?, ?, ?, ?, ?, ?)",
                           (f_name, l_name, email, "haslo123", "USER", random.randint(1, N_DEPT)))

        # 6. BIURKA
        print(f"Biurka ({N_BIURKA})...")
        strefy = ['Strefa Ciszy', 'Open Space', 'Przy oknie', 'Chillout']
        for i in range(N_BIURKA):
            cursor.execute("INSERT INTO Biurka (id_pietra, kod_biurka, id_typu, strefa, czy_sprawne) VALUES (?, ?, ?, ?, ?)",
                           (random.randint(1, N_PIETRA), f"D-{i:03d}", random.randint(1, 2), random.choice(strefy), 1))

        # 7. WYPOSAŻENIE
        print(f"Wyposażenie ({N_WYPOSAZENIE})...")
        sprzety = ['Monitor 27"', 'Klawiatura', 'Stacja dokująca', 'Lampka']
        for _ in range(N_WYPOSAZENIE):
            cursor.execute("INSERT INTO Wyposazenie (id_biurka, nazwa_sprzetu, numer_seryjny) VALUES (?, ?, ?)",
                           (random.randint(1, N_BIURKA), random.choice(sprzety), fake.bothify(text='??-####-####').upper()))

        # 8. REZERWACJE
        print(f"Rezerwacje ({N_REZERWACJE})...")
        for _ in range(N_REZERWACJE):
            data = (datetime.now() + timedelta(days=random.randint(-7, 7))).strftime('%Y-%m-%d')
            h_start = random.randint(7, 15)
            cursor.execute("INSERT INTO Rezerwacje (id_pracownika, id_biurka, data_rezerwacji, godzina_start, godzina_koniec, id_statusu) VALUES (?, ?, ?, ?, ?, ?)",
                           (random.randint(1, N_PRACOWNICY), random.randint(1, N_BIURKA), data, h_start, h_start + random.randint(2, 5), 1))

        # 9. USTERKI
        print(f"Usterki ({N_USTERKI})...")
        for _ in range(N_USTERKI):
            cursor.execute("INSERT INTO Usterki (id_biurka, opis) VALUES (?, ?)", 
                           (random.randint(1, N_BIURKA), random.choice(['Zepsuty ekran', 'Brak prądu', 'Uszkodzony fotel'])))

        # 10. ZAMIANY
        print(f"Zamiany ({N_ZAMIANY})...")
        for _ in range(N_ZAMIANY):
            cursor.execute("INSERT INTO Zamiany (id_nadawcy, id_odbiorcy, id_rez_nadawcy, id_rez_odbiorcy, status) VALUES (?, ?, ?, ?, ?)",
                           (random.randint(1, N_PRACOWNICY), random.randint(1, N_PRACOWNICY), random.randint(1, N_REZERWACJE), random.randint(1, N_REZERWACJE), 'OCZEKUJACE'))

        # 11. LOGI
        print(f"Logi ({N_LOGI})...")
        for _ in range(N_LOGI):
            cursor.execute("INSERT INTO Logi_Systemowe (operacja, opis) VALUES (?, ?)", 
                           (random.choice(['LOGIN', 'LOGOUT', 'RESERVATION_ADD']), fake.sentence()))

        conn.commit()
        print("\n✅ Gotowe! Twoja baza została zasilona inteligentnymi danymi.")

    except Exception as e:
        print(f"\n❌ Błąd podczas generowania: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    generate_intelligent_data()