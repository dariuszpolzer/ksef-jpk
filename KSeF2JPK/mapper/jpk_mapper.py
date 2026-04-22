from collections import defaultdict

from KSeF2JPK.model.jpk_model import WierszEwidencji


class JPKMapperPRO:
    def map(self, faktura):
        """
        Zwraca listę WierszEwidencji.
        Jedna faktura może dać:
        - 1 wiersz, jeśli ma jedną stawkę,
        - wiele wierszy, jeśli ma wiele stawek.
        """

        typ = faktura.meta.get("typ", "nieznany")
        pozycje = faktura.pozycje or []

        if typ not in ("sprzedaz", "zakup"):
            raise ValueError(
                f"Nieznany typ faktury dla dokumentu: "
                f"{faktura.meta.get('numer') or faktura.nr_ksef or 'BRAK'}"
            )

        if typ == "sprzedaz":
            nip_kontrahenta = (faktura.meta.get("nip_nabywcy") or "").strip()
            nazwa_kontrahenta = (faktura.meta.get("nazwa_nabywcy") or "").strip()
        else:
            nip_kontrahenta = (faktura.meta.get("nip_sprzedawcy") or "").strip()
            nazwa_kontrahenta = (faktura.meta.get("nazwa_sprzedawcy") or "").strip()

        nr_ksef = faktura.nr_ksef or faktura.meta.get("nr_ksef", "")
        dokument = faktura.meta.get("numer") or nr_ksef or "BRAK"

        data_wystawienia = faktura.meta.get("data_wystawienia")
        data_sprzedazy = faktura.meta.get("data_sprzedazy")
        data_wplywu = faktura.meta.get("data_wplywu") if typ == "zakup" else None

        # Fallbacki z klasyfikatora zapisane na poziomie faktury
        meta_gtu = faktura.meta.get("gtu")
        meta_procedury = sorted(set(faktura.meta.get("procedury", [])))

        # Grupowanie pozycji wg stawki
        # None = np. ZW / NP / OO
        grupy = defaultdict(list)
        for p in pozycje:
            grupy[p.stawka].append(p)

        wynik = []

        for stawka, grupa_pozycji in grupy.items():
            netto = round(sum((p.netto or 0) for p in grupa_pozycji), 2)
            vat = round(sum((p.vat or 0) for p in grupa_pozycji), 2)

            # GTU z pozycji
            gtu_values = sorted({p.gtu for p in grupa_pozycji if p.gtu})

            if len(gtu_values) == 1:
                gtu = gtu_values[0]
            elif len(gtu_values) > 1:
                # kolizja GTU w jednej grupie stawek – nie zgadujemy
                gtu = None
            else:
                # fallback do klasyfikacji na poziomie faktury
                gtu = meta_gtu

            # Procedury z pozycji
            procedury_from_positions = sorted({
                proc
                for p in grupa_pozycji
                for proc in (p.procedury or [])
                if proc
            })

            if procedury_from_positions:
                procedury = procedury_from_positions
            else:
                # fallback do klasyfikacji na poziomie faktury
                procedury = meta_procedury

            wynik.append(
                WierszEwidencji(
                    typ=typ,
                    netto=netto,
                    vat=vat,
                    stawka=stawka,
                    kontrahent_nip=nip_kontrahenta,
                    kontrahent_nazwa=nazwa_kontrahenta,
                    nr_ksef=nr_ksef,
                    dokument=dokument,
                    data_wystawienia=data_wystawienia,
                    data_sprzedazy=data_sprzedazy,
                    data_wplywu=data_wplywu,
                    gtu=gtu,
                    procedury=procedury,
                )
            )

        # Sortowanie dla przewidywalności testów:
        # 23, 8, 5, 0, None na końcu
        def sort_key(w):
            if w.stawka is None:
                return 999
            return -float(w.stawka)

        wynik.sort(key=sort_key)
        return wynik