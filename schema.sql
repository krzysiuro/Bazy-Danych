-- CZYSZCZENIE --
DROP VIEW IF EXISTS VW_RAPORT_OBLOZENIA;
DROP VIEW IF EXISTS VW_USTERKOWOSC;
DROP TRIGGER IF EXISTS TR_LOG_REZERWACJA;
DROP TRIGGER IF EXISTS TR_AUTO_AWARIA;
DROP TABLE IF EXISTS Logi_Systemowe;
DROP TABLE IF EXISTS Strefy_Dostepu;
DROP TABLE IF EXISTS Usterki;
DROP TABLE IF EXISTS Zamiany;
DROP TABLE IF EXISTS Rezerwacje;
DROP TABLE IF EXISTS Wyposazenie;
DROP TABLE IF EXISTS Biurka;
DROP TABLE IF EXISTS Pracownicy;
DROP TABLE IF EXISTS Departamenty;
DROP TABLE IF EXISTS Pietra;
DROP TABLE IF EXISTS Budynki;
DROP TABLE IF EXISTS S_Statusy_Usterki;
DROP TABLE IF EXISTS S_Statusy_Rezerwacji;
DROP TABLE IF EXISTS S_Typy_Biurek;

PRAGMA foreign_keys = ON;

-- 1. SŁOWNIKI
CREATE TABLE S_Typy_Biurek (id_typu INTEGER PRIMARY KEY AUTOINCREMENT, nazwa TEXT UNIQUE);
CREATE TABLE S_Statusy_Rezerwacji (id_statusu INTEGER PRIMARY KEY AUTOINCREMENT, nazwa TEXT UNIQUE);
CREATE TABLE S_Statusy_Usterki (id_statusu INTEGER PRIMARY KEY AUTOINCREMENT, nazwa TEXT UNIQUE NOT NULL);

-- 2. STRUKTURA
CREATE TABLE Budynki (id_budynku INTEGER PRIMARY KEY AUTOINCREMENT, nazwa TEXT, adres TEXT);
CREATE TABLE Pietra (id_pietra INTEGER PRIMARY KEY AUTOINCREMENT, id_budynku INTEGER REFERENCES Budynki(id_budynku), numer_pietra INTEGER);
CREATE TABLE Departamenty (id_departamentu INTEGER PRIMARY KEY AUTOINCREMENT, nazwa_dept TEXT);

CREATE TABLE Pracownicy (
    id_pracownika INTEGER PRIMARY KEY AUTOINCREMENT,
    imie TEXT,
    nazwisko TEXT,
    email TEXT UNIQUE,
    haslo TEXT,
    rola TEXT DEFAULT 'USER',
    id_departamentu INTEGER REFERENCES Departamenty(id_departamentu)
);

-- 3. ZASOBY
CREATE TABLE Biurka (
    id_biurka INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pietra INTEGER REFERENCES Pietra(id_pietra),
    kod_biurka TEXT UNIQUE,
    id_typu INTEGER REFERENCES S_Typy_Biurek(id_typu),
    strefa TEXT,
    czy_sprawne INTEGER DEFAULT 1
);

CREATE TABLE Wyposazenie (
    id_sprzetu INTEGER PRIMARY KEY AUTOINCREMENT,
    id_biurka INTEGER REFERENCES Biurka(id_biurka),
    nazwa_sprzetu TEXT,
    numer_seryjny TEXT
);

-- 4. OPERACJE
CREATE TABLE Rezerwacje (
    id_rezerwacji INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pracownika INTEGER REFERENCES Pracownicy(id_pracownika),
    id_biurka INTEGER REFERENCES Biurka(id_biurka),
    data_rezerwacji TEXT,
    godzina_start INTEGER,
    godzina_koniec INTEGER,
    id_statusu INTEGER DEFAULT 1,
    data_utworzenia DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Usterki (
    id_usterki INTEGER PRIMARY KEY AUTOINCREMENT,
    id_biurka INTEGER REFERENCES Biurka(id_biurka),
    opis TEXT,
    data_zgloszenia DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 5. AUDYT I DOSTĘP
CREATE TABLE Strefy_Dostepu (
    id_strefy INTEGER PRIMARY KEY AUTOINCREMENT,
    id_departamentu INTEGER REFERENCES Departamenty(id_departamentu),
    id_pietra INTEGER REFERENCES Pietra(id_pietra)
);

CREATE TABLE Logi_Systemowe (
    id_logu INTEGER PRIMARY KEY AUTOINCREMENT,
    operacja TEXT,
    opis TEXT,
    data_logu DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Zamiany (
    id_zamiany INTEGER PRIMARY KEY AUTOINCREMENT,
    id_nadawcy INTEGER REFERENCES Pracownicy(id_pracownika),
    id_odbiorcy INTEGER REFERENCES Pracownicy(id_pracownika),
    id_rez_nadawcy INTEGER REFERENCES Rezerwacje(id_rezerwacji) ON DELETE CASCADE, -- DODANO TO
    id_rez_odbiorcy INTEGER REFERENCES Rezerwacje(id_rezerwacji) ON DELETE CASCADE, -- I TO
    status TEXT DEFAULT 'OCZEKUJACE'
);

-- 6. WIDOKI
CREATE VIEW VW_RAPORT_OBLOZENIA AS
SELECT 
    bud.nazwa as BUDYNEK, 
    COUNT(DISTINCT b.id_biurka) as WSZYSTKIE_BIURKA,
    (SELECT COUNT(*) FROM Rezerwacje r2 
     JOIN Biurka b2 ON r2.id_biurka = b2.id_biurka
     JOIN Pietra p2 ON b2.id_pietra = p2.id_pietra
     WHERE p2.id_budynku = bud.id_budynku AND r2.data_rezerwacji = date('now')) as ZAREZERWOWANE_DZIS
FROM Budynki bud
JOIN Pietra p ON bud.id_budynku = p.id_budynku
JOIN Biurka b ON p.id_pietra = b.id_pietra
GROUP BY bud.nazwa;

CREATE VIEW VW_USTERKOWOSC AS
SELECT b.kod_biurka, COUNT(u.id_usterki) as SUMA_PROBLEMOW
FROM Biurka b
JOIN Usterki u ON b.id_biurka = u.id_biurka
GROUP BY b.kod_biurka;

-- 7. TRIGGERY
CREATE TRIGGER TR_LOG_REZERWACJA AFTER INSERT ON Rezerwacje
BEGIN
    INSERT INTO Logi_Systemowe (operacja, opis) 
    VALUES ('INSERT', 'Nowa rezerwacja ID: ' || NEW.id_rezerwacji);
END;

CREATE TRIGGER TR_AUTO_AWARIA AFTER INSERT ON Usterki
BEGIN
    UPDATE Biurka SET czy_sprawne = 0 WHERE id_biurka = NEW.id_biurka;
END;

-- 8. DANE TESTOWE (PO JEDNYM REKORDZIE, BEZ DUBLETY!)
INSERT INTO S_Typy_Biurek (nazwa) VALUES ('Hot-desk'), ('Dedykowane');
INSERT INTO S_Statusy_Usterki (nazwa) VALUES ('NOWE'), ('W NAPRAWIE');
INSERT INTO S_Statusy_Rezerwacji (nazwa) VALUES ('PLANOWANA'), ('ANULOWANA');
INSERT INTO Budynki (nazwa, adres) VALUES ('Olivia Star', 'Gdańsk'), ('Alchemia', 'Gdańsk');
INSERT INTO Pietra (id_budynku, numer_pietra) VALUES (1, 10), (2, 5);
INSERT INTO Departamenty (nazwa_dept) VALUES ('IT'), ('HR');

-- Konta pracowników
INSERT INTO Pracownicy (imie, nazwisko, email, haslo, rola, id_departamentu) 
VALUES ('System', 'Admin', 'admin@firma.pl', 'admin123', 'ADMIN', 1);
INSERT INTO Pracownicy (imie, nazwisko, email, haslo, rola, id_departamentu) 
VALUES ('Adam', 'Nowak', 'adam@firma.pl', 'adam123', 'USER', 1);

-- Biurka z opisami
INSERT INTO Biurka (id_pietra, kod_biurka, id_typu, strefa) VALUES (1, 'B-101', 1, 'Strefa Ciszy');
INSERT INTO Biurka (id_pietra, kod_biurka, id_typu, strefa) VALUES (1, 'B-102', 2, 'Open Space (Okienko)');
INSERT INTO Biurka (id_pietra, kod_biurka, id_typu, strefa) VALUES (2, 'A-505', 1, 'Strefa Chillout');