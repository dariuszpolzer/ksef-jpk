\# 📌 Backlog projektu ksef2jpk  

Kompletny zestaw ISSUE (BUG + FEATURE + IMPROVEMENT + TESTS) wynikający z audytu projektu.



\---



\## ISSUE 1 — FEATURE: Obsługa korekt (KOR)



\### Opis

Parser wykrywa faktury korygujące (`RodzajFaktury = KOR`), ale pipeline nie księguje ich w JPK. Powoduje to niezgodność z MF i ryzyko błędnych deklaracji.



\### Kroki do odtworzenia

1\. Wrzucić fakturę KSeF typu KOR.

2\. Uruchomić pipeline.

3\. Wygenerowany JPK nie zawiera korekty.


# Priorytety ISSUE

## P1 — Krytyczne
- ISSUE 1 — Obsługa korekt (KOR)
- ISSUE 2 — Walidacja sum faktury
- ISSUE 3 — Obsługa wielu stawek VAT
- ISSUE 7 — Odporność na błędne XML

## P2 — Wysoki priorytet
- ISSUE 5 — Walidacja danych wejściowych
- ISSUE 4 — Udoskonalenie GTU i procedur
- ISSUE 9 — Obsługa odwrotnego obciążenia / importu usług

## P3 — Średni priorytet
- ISSUE 6 — Logowanie audytowe
- ISSUE 8 — Testy integracyjne

## P4 — Niski priorytet
- ISSUE 10 — Wersjonowanie schemy MF



\### Oczekiwane zachowanie

\- Korekty są księgowane zgodnie z logiką MF.

\- Wiersze ewidencji odzwierciedlają wartości korekty.

\- Raport jakości pokazuje liczbę korekt.



\### Rzeczywiste zachowanie

\- Korekty są wykrywane, ale ignorowane w JPK.



\### Proponowane rozwiązanie

\- Rozszerzyć parser o pełne dane korekty.

\- Dodać logikę księgowania w mapperze.

\- Dodać obsługę korekt w builderze.

\- Dodać testy integracyjne.



\### Pliki

\- `ksef2jpk/parser/ksef\_parser.py`

\- `ksef2jpk/mapper/jpk\_mapper.py`

\- `ksef2jpk/builder/jpk\_builder.py`



\### Kryteria akceptacji

\- Korekty są poprawnie księgowane.

\- JPK przechodzi walidację XSD.

\- Testy obejmują min. 3 scenariusze korekt.



\---



\## ISSUE 2 — BUG: Brak walidacji sum faktury (netto/VAT/brutto)



\### Opis

Projekt nie weryfikuje zgodności sum faktury:

\- suma pozycji netto ≠ wartość netto z nagłówka,

\- suma VAT ≠ VAT z nagłówka,

\- brutto ≠ netto + VAT.



\### Kroki do odtworzenia

1\. Wrzucić fakturę z błędnymi sumami.

2\. Uruchomić pipeline.

3\. JPK generuje się bez ostrzeżeń.



\### Oczekiwane zachowanie

\- System wykrywa niespójności.

\- Raport jakości zawiera ostrzeżenia lub błędy.

\- JPK nie jest generowany przy błędzie krytycznym.



\### Rzeczywiste zachowanie

\- Brak walidacji.

\- JPK generuje się mimo błędów.



\### Proponowane rozwiązanie

\- Dodać walidację sum w parserze lub mapperze.

\- Wprowadzić poziomy błędów (WARNING/ERROR).

\- Rozszerzyć raport jakości.



\### Pliki

\- `ksef2jpk/parser/ksef\_parser.py`

\- `ksef2jpk/mapper/jpk\_mapper.py`



\### Kryteria akceptacji

\- Błędne sumy są wykrywane.

\- Raport jakości je pokazuje.

\- Testy obejmują 3 scenariusze błędów sum.



\---



\## ISSUE 3 — FEATURE: Obsługa faktur z wieloma stawkami VAT



\### Opis

Mapper zakłada jedną stawkę VAT na fakturę. Faktury z wieloma stawkami są księgowane błędnie.



\### Kroki do odtworzenia

1\. Wrzucić fakturę z pozycjami 23% + 8%.

2\. Uruchomić pipeline.

3\. JPK zawiera tylko jedną stawkę.



\### Oczekiwane zachowanie

\- Każda stawka generuje osobny wiersz ewidencji.

\- Deklaracja VAT ma poprawne sumy P\_19–P\_24.



\### Rzeczywiste zachowanie

\- Mapper generuje jeden wiersz.



\### Proponowane rozwiązanie

\- Rozszerzyć model faktury o listę pozycji.

\- Mapper generuje wiele wierszy.

\- Builder sumuje wartości per stawka.



\### Pliki

\- `ksef2jpk/model/faktura\_model.py`

\- `ksef2jpk/mapper/jpk\_mapper.py`

\- `ksef2jpk/builder/jpk\_builder.py`



\### Kryteria akceptacji

\- Faktury z wieloma stawkami są poprawnie księgowane.

\- Testy obejmują min. 3 kombinacje stawek.



\---



\## ISSUE 4 — IMPROVEMENT: Udoskonalenie klasyfikacji GTU i procedur



\### Opis

Klasyfikacja GTU/MPP/TP/EE/WDT/IMP opiera się na prostych heurystykach. Może prowadzić do błędnych klasyfikacji.



\### Kroki do odtworzenia

1\. Wrzucić fakturę wymagającą GTU.

2\. Pipeline nie przypisuje GTU.



\### Oczekiwane zachowanie

\- GTU i procedury są przypisywane deterministycznie.

\- Niepewne klasyfikacje są raportowane.



\### Rzeczywiste zachowanie

\- Heurystyki są zbyt proste.



\### Proponowane rozwiązanie

\- Dodać reguły oparte na danych z faktury.

\- Dodać konfigurację reguł w `config.json`.

\- Raportować niepewne klasyfikacje.



\### Pliki

\- `ksef2jpk/classifier/jpk\_flags.py`



\### Kryteria akceptacji

\- GTU/procedury są stabilne i powtarzalne.

\- Testy obejmują min. 10 scenariuszy.



\---



\## ISSUE 5 — BUG: Brak walidacji danych wejściowych (NIP, daty, pola obowiązkowe)



\### Opis

Parser nie waliduje:

\- NIP kontrahenta,

\- dat (np. DataSprzedazy > DataWystawienia),

\- brakujących pól obowiązkowych.



\### Kroki do odtworzenia

1\. Wrzucić fakturę z błędnym NIP.

2\. Pipeline generuje JPK bez ostrzeżeń.



\### Oczekiwane zachowanie

\- Błędne dane są wykrywane.

\- Raport jakości je pokazuje.



\### Rzeczywiste zachowanie

\- Brak walidacji.



\### Proponowane rozwiązanie

\- Dodać walidację w parserze.

\- Dodać ostrzeżenia w raporcie jakości.



\### Pliki

\- `ksef2jpk/parser/ksef\_parser.py`



\### Kryteria akceptacji

\- Błędne dane są wykrywane.

\- Testy obejmują min. 5 scenariuszy błędów.



\---



\## ISSUE 6 — FEATURE: Logowanie audytowe



\### Opis

Projekt nie zapisuje:

\- kiedy wygenerowano JPK,

\- z jakich plików,

\- jakie błędy wykryto.



\### Oczekiwane zachowanie

\- Każde uruchomienie generuje log audytowy.



\### Proponowane rozwiązanie

\- Dodać logger (plik `logs/jpk.log`).

\- Logować każdy etap pipeline.

\- Maskować dane wrażliwe.



\### Pliki

\- `ksef2jpk/main.py`

\- `ksef2jpk/utils/`



\### Kryteria akceptacji

\- Log zawiera pełną historię generowania JPK.



\---



\## ISSUE 7 — BUG: Parser nie jest odporny na błędne XML



\### Opis

Błędny XML powoduje crash pipeline.



\### Kroki do odtworzenia

1\. Wrzucić uszkodzony plik XML.

2\. Pipeline przerywa działanie.



\### Oczekiwane zachowanie

\- Błędne XML są pomijane.

\- Raport jakości pokazuje liczbę odrzuconych plików.



\### Proponowane rozwiązanie

\- Dodać try/except w parserze.

\- Dodać walidację struktury XML.



\### Pliki

\- `ksef2jpk/parser/ksef\_parser.py`



\### Kryteria akceptacji

\- Pipeline działa mimo błędnych XML.



\---



\## ISSUE 8 — TESTS: Testy integracyjne z realnymi fakturami KSeF



\### Opis

Brak testów end-to-end.



\### Proponowane rozwiązanie

\- Dodać katalog `test\_data/real/`.

\- Dodać testy integracyjne:

&#x20; - sprzedaż,

&#x20; - zakup,

&#x20; - korekty,

&#x20; - wiele stawek,

&#x20; - MPP,

&#x20; - WDT/EXP.



\### Pliki

\- `tests/test\_full\_pipeline.py`



\### Kryteria akceptacji

\- Pipeline przechodzi testy dla wszystkich scenariuszy.



\---



\## ISSUE 9 — FEATURE: Obsługa odwrotnego obciążenia / importu usług



\### Opis

Brak logiki dla:

\- IMP,

\- odwrotnego obciążenia,

\- importu usług.



\### Proponowane rozwiązanie

\- Rozszerzyć mapper i builder.

\- Dodać pola K\_45–K\_47.

\- Dodać testy.



\### Pliki

\- `ksef2jpk/mapper/jpk\_mapper.py`

\- `ksef2jpk/builder/jpk\_builder.py`



\### Kryteria akceptacji

\- Faktury importowe są poprawnie księgowane.



\---



\## ISSUE 10 — IMPROVEMENT: Wersjonowanie schemy JPK\_V7M



\### Opis

Projekt zakłada jedną wersję XSD, ale MF aktualizuje schemy.



\### Proponowane rozwiązanie

\- Dodać obsługę wielu wersji XSD.

\- Dodać wybór wersji w `config.json`.



\### Pliki

\- `ksef2jpk/validator/validate\_jpk.py`



\### Kryteria akceptacji

\- Projekt obsługuje min. 2 wersje schemy.





