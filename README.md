Enterprise Desk Management System (EDMS)
Autorzy: Maja Drohobycka, Krzysztof Rodzinka
Temat projektu: System zarządzania i rezerwacji stanowisk pracy w przestrzeni coworkingowej klasy Enterprise.

1. Opis projektu
   Projekt realizuje kompleksowy system do zarządzania zasobami biurowymi w dużym przedsiębiorstwie. System pozwala pracownikom na samodzielną rejestrację, rezerwację biurek w różnych budynkach i strefach (np. strefa ciszy, open space) oraz interakcję z innymi użytkownikami (system wymiany rezerwacji). Administratorzy posiadają pełny wgląd w analitykę obłożenia oraz stan techniczny infrastruktury.
2. Wykorzystane technologie
   Język programowania: Python 3.11+
   Biblioteka interfejsu (Frontend): Streamlit (zapewnia dynamiczny, responsywny interfejs webowy).
   Silnik bazy danych: SQLite (relacyjna baza danych w pełni wspierająca transakcje ACID).
   Analiza danych: Pandas (do przetwarzania wyników zapytań SQL).
   Generator danych: Faker (zastosowany do zasilenia bazy tysiącami realistycznych rekordów testowych).
3. Aspekty techniczne bazy danych
   Model Danych (14 tabel)
   Baza danych została zaprojektowana w oparciu o model relacyjny, obejmujący słowniki (S\_), strukturę organizacyjną (Budynki, Departamenty, Pracownicy) oraz tabele operacyjne (Rezerwacje, Usterki, Zamiany).
   Operacje Złożone i Transakcje
   Proces Rezerwacji: Zaimplementowano atomową transakcję sprawdzającą spójność danych. System weryfikuje jednocześnie: sprawność biurka, dostępność w danym dniu oraz brak nakładania się przedziałów godzinowych.
   System Wymiany: Wykorzystano transakcję do jednoczesnej zamiany właścicieli dwóch rezerwacji w tabeli Rezerwacje wraz z aktualizacją statusu prośby w tabeli Zamiany.
   Raportowanie i Agregacja
   Widok VW_RAPORT_OBLOZENIA: Złożone zapytanie łączące 4 tabele, obliczające dynamicznie procentowe obłożenie biur dla każdego budynku na bieżący dzień.
   Widok VW_USTERKOWOSC: Agregacja danych z tabeli Usterki w celu wyłonienia najbardziej awaryjnych stanowisk pracy.
   Automatyzacja (Triggery)
   TR_AUTO_AWARIA: Automatycznie zmienia status biurka na niesprawne w momencie zgłoszenia usterki przez pracownika.
   TR_LOG_REZERWACJA: Tworzy wpisy w dzienniku audytowym po każdej nowej rezerwacji.

   Projekt został przygotowany w sposób zautomatyzowany. Przy pierwszym uruchomieniu system sam stworzy plik bazy danych i zainicjuje strukturę.
   Krok 1: Pobranie repozytorium

   git clone https://github.com/[Twoja_Nazwa_Uzytkownika]/[Nazwa_Repozytorium]
   cd [Nazwa_Repozytorium]

   Krok 2: Instalacja bibliotek
   Zalecane jest użycie środowiska wirtualnego. Wymagane biblioteki znajdują się w pliku requirements.txt.

   pip install -r requirements.txt

   Krok 3: Generowanie danych testowych (Opcjonalnie)
   Aby baza zawierała tysiące rekordów do testów wydajnościowych, należy uruchomić generator:

   python generator.py

   Krok 4: Uruchomienie aplikacji
   Aplikacja zostanie otwarta w domyślnej przeglądarce pod adresem http://localhost:8501.

   streamlit run app.py

4. Dane do testów (Konta)
   Administrator: admin@firma.pl | hasło: admin123
   Pracownik (przykład): adam@firma.pl | hasło: adam123
   Istnieje również możliwość stworzenia własnego konta przez formularz Rejestracja.

   Uwagi do walidacji:
   Wszystkie operacje w systemie posiadają walidację komunikatów (Success/Error/Warning).
   System blokuje rezerwacje powyżej 7 dni w przód.
   Interfejs admina pozwala na "naprawę" biurek, co przywraca je do widoku rezerwacji dla pracowników.
