import os
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from defusedxml import ElementTree as ET

from ksef2jpk.model.faktura_model import FakturaModel, Kontrahent, Pozycja
from ksef2jpk.utils.ksef_number import extract_ksef_number_from_filename


class KSeFParser:
    EU_COUNTRIES = {
        "AT",
        "BE",
        "BG",
        "CY",
        "CZ",
        "DE",
        "DK",
        "EE",
        "ES",
        "FI",
        "FR",
        "GR",
        "HR",
        "HU",
        "IE",
        "IT",
        "LT",
        "LU",
        "LV",
        "MT",
        "NL",
        "PL",
        "PT",
        "RO",
        "SE",
        "SI",
        "SK",
    }

    def __init__(self, my_nip: str):
        self.MY_NIP = str(my_nip or "").strip()

    def _text(self, el):
        if el is None or el.text is None:
            return ""
        return el.text.strip()

    def _decimal_or_none(self, text):
        if text is None:
            return None

        text = text.strip().replace(",", ".")
        if not text:
            return None

        try:
            return Decimal(text)
        except InvalidOperation:
            return None

    def _get_ns(self, root):
        if root.tag.startswith("{"):
            uri = root.tag.split("}")[0][1:]
            return {"fa": uri}
        return {}

    def _find_text_first(self, root, paths, ns):
        for path in paths:
            try:
                el = root.find(path, ns)
            except SyntaxError:
                continue

            txt = self._text(el)
            if txt:
                return txt

        return ""

    def _podmiot_nazwa(self, root, podmiot_tag, ns):
        candidates = [
            f".//fa:{podmiot_tag}/fa:DaneIdentyfikacyjne/fa:Nazwa",
            f".//fa:{podmiot_tag}/fa:DaneIdentyfikacyjne/fa:NazwaPelna",
            f".//fa:{podmiot_tag}/fa:DaneIdentyfikacyjne/fa:PelnaNazwa",
            f".//fa:{podmiot_tag}/fa:DaneIdentyfikacyjne/fa:ImiePierwsze",
        ]
        return self._find_text_first(root, candidates, ns)

    def _podmiot_kraj(self, root, podmiot_tag, ns):
        candidates = [
            f".//fa:{podmiot_tag}/fa:Adres/fa:KodKraju",
            f".//fa:{podmiot_tag}//fa:KodKraju",
        ]
        return self._find_text_first(root, candidates, ns) or "PL"

    def _normalize_stawka(self, raw):
        return (raw or "").strip().upper()

    def _is_close(self, a, b, tolerance=Decimal("0.01")):
        return abs(a - b) <= tolerance

    def _normalize_correction_sign(
        self,
        netto_dec: Decimal,
        vat_dec: Decimal,
        is_korekta: bool,
    ):
        if not is_korekta:
            return netto_dec, vat_dec

        return -abs(netto_dec), -abs(vat_dec)

    def _is_valid_nip(self, nip: str) -> bool:
        nip = "".join(ch for ch in str(nip or "") if ch.isdigit())

        if len(nip) != 10:
            return False

        weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
        checksum = sum(int(nip[i]) * weights[i] for i in range(9)) % 11

        return checksum != 10 and checksum == int(nip[9])

    def _is_valid_iso_date(self, value: str) -> bool:
        if not value:
            return False

        try:
            from datetime import date

            date.fromisoformat(value[:10])
            return True
        except ValueError:
            return False

    def _build_input_validation(self, meta: dict, pozycje: list) -> dict:
        warnings = []

        typ = meta.get("typ")

        if typ not in ("sprzedaz", "zakup"):
            warnings.append("Nieznany typ faktury - podatnik nie jest ani sprzedawcą, ani nabywcą.")

        if not meta.get("numer"):
            warnings.append("Brak numeru faktury P_2.")

        if not meta.get("data_wystawienia"):
            warnings.append("Brak daty wystawienia P_1.")
        elif not self._is_valid_iso_date(meta.get("data_wystawienia")):
            warnings.append(f"Nieprawidłowa data wystawienia: {meta.get('data_wystawienia')!r}.")

        if typ == "sprzedaz":
            if not meta.get("data_sprzedazy"):
                warnings.append("Brak daty sprzedaży P_6 dla faktury sprzedażowej.")

            if not self._is_valid_nip(meta.get("nip_nabywcy")):
                warnings.append(f"Nieprawidłowy NIP nabywcy: {meta.get('nip_nabywcy')!r}.")

            if not meta.get("nazwa_nabywcy"):
                warnings.append("Brak nazwy nabywcy.")

        if typ == "zakup":
            if not self._is_valid_nip(meta.get("nip_sprzedawcy")):
                warnings.append(f"Nieprawidłowy NIP sprzedawcy: {meta.get('nip_sprzedawcy')!r}.")

            if not meta.get("nazwa_sprzedawcy"):
                warnings.append("Brak nazwy sprzedawcy.")

        if not pozycje:
            warnings.append("Brak pozycji faktury FaWiersz.")

        return {
            "ok": not warnings,
            "warnings": warnings,
            "warning_count": len(warnings),
        }

    def _sum_header_by_prefix(self, root, prefixes) -> Decimal:
        total = Decimal("0.00")

        for el in root.iter():
            tag = el.tag.split("}", 1)[-1]

            if any(tag.startswith(prefix) for prefix in prefixes):
                value = self._decimal_or_none(self._text(el))

                if value is not None:
                    total += value

        return total

    def _build_totals_check(self, pozycje, meta):
        netto_poz = sum((Decimal(str(p.netto)) for p in pozycje), Decimal("0.00"))
        vat_poz = sum((Decimal(str(p.vat)) for p in pozycje), Decimal("0.00"))
        brutto_poz = netto_poz + vat_poz

        netto_nag = self._decimal_or_none(meta.get("suma_netto_naglowek")) or Decimal("0.00")
        vat_nag = self._decimal_or_none(meta.get("suma_vat_naglowek")) or Decimal("0.00")
        brutto_nag = self._decimal_or_none(meta.get("suma_brutto_naglowek")) or Decimal("0.00")

        is_korekta = bool(meta.get("is_korekta"))

        result = {
            "pozycje_netto": float(netto_poz),
            "pozycje_vat": float(vat_poz),
            "pozycje_brutto": float(brutto_poz),
            "naglowek_netto": float(netto_nag),
            "naglowek_vat": float(vat_nag),
            "naglowek_brutto": float(brutto_nag),
            "is_korekta": is_korekta,
        }

        if is_korekta:
            # Dla KOR parser księgowo przekształca wartości do JPK:
            # - bierze tylko StanPrzed,
            # - odwraca znak na minus.
            # Nagłówek KSeF może pokazywać wartości po korekcie, np. P_15 = 0,
            # więc zwykłe porównanie pozycji z nagłówkiem daje fałszywy warning.
            result.update(
                {
                    "netto_ok": True,
                    "vat_ok": True,
                    "brutto_ok": True,
                    "all_ok": True,
                    "mode": "kor_skip_header_compare",
                }
            )
            return result

        result["netto_ok"] = self._is_close(netto_poz, netto_nag)
        result["vat_ok"] = self._is_close(vat_poz, vat_nag)
        result["brutto_ok"] = self._is_close(brutto_poz, brutto_nag)
        result["all_ok"] = result["netto_ok"] and result["vat_ok"] and result["brutto_ok"]
        result["mode"] = "standard"

        return result

    def parse(self, xml_path):
        meta = {}
        pozycje = []

        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = self._get_ns(root)

        filename = os.path.basename(xml_path)

        data_wystawienia = self._find_text_first(
            root,
            [".//fa:Fa/fa:P_1", ".//fa:P_1"],
            ns,
        )

        numer = self._find_text_first(
            root,
            [".//fa:Fa/fa:P_2", ".//fa:P_2"],
            ns,
        )

        rodzaj_faktury = self._find_text_first(
            root,
            [".//fa:Fa/fa:RodzajFaktury", ".//fa:RodzajFaktury"],
            ns,
        )

        mpp_flag = self._find_text_first(
            root,
            [
                ".//fa:Fa/fa:Adnotacje/fa:MPP",
                ".//fa:Adnotacje/fa:MPP",
                ".//fa:MPP",
            ],
            ns,
        )

        przyczyna_korekty = self._find_text_first(
            root,
            [".//fa:Fa/fa:PrzyczynaKorekty", ".//fa:PrzyczynaKorekty"],
            ns,
        )

        nr_fa_korygowanej = self._find_text_first(
            root,
            [
                ".//fa:Fa/fa:DaneFaKorygowanej/fa:NrFaKorygowanej",
                ".//fa:DaneFaKorygowanej/fa:NrFaKorygowanej",
                ".//fa:NrFaKorygowanej",
            ],
            ns,
        )

        data_fa_korygowanej = self._find_text_first(
            root,
            [
                ".//fa:Fa/fa:DaneFaKorygowanej/fa:DataFaKorygowanej",
                ".//fa:DaneFaKorygowanej/fa:DataFaKorygowanej",
                ".//fa:DataFaKorygowanej",
            ],
            ns,
        )

        data_sprzedazy = self._find_text_first(
            root,
            [
                ".//fa:Fa/fa:P_6",
                ".//fa:P_6",
                ".//fa:Fa/fa:OkresFa/fa:P_6_Do",
                ".//fa:OkresFa/fa:P_6_Do",
                ".//fa:Fa/fa:OkresFa/fa:P_6_Od",
                ".//fa:OkresFa/fa:P_6_Od",
            ],
            ns,
        )

        nr_ksef = self._find_text_first(root, [".//fa:NrKSeF"], ns)

        nr_ksef_from_filename = ""
        if not nr_ksef:
            nr_ksef_from_filename = extract_ksef_number_from_filename(filename)
            if nr_ksef_from_filename:
                nr_ksef = nr_ksef_from_filename

        sprzedawca_nip = self._find_text_first(
            root,
            [
                ".//fa:Podmiot1/fa:DaneIdentyfikacyjne/fa:NIP",
                ".//fa:Podmiot1//fa:NIP",
            ],
            ns,
        )
        sprzedawca_nazwa = self._podmiot_nazwa(root, "Podmiot1", ns)
        sprzedawca_kraj = self._podmiot_kraj(root, "Podmiot1", ns)
        nabywca_nip = self._find_text_first(
            root,
            [
                ".//fa:Podmiot2/fa:DaneIdentyfikacyjne/fa:NIP",
                ".//fa:Podmiot2//fa:NIP",
            ],
            ns,
        )
        nabywca_nazwa = self._podmiot_nazwa(root, "Podmiot2", ns)
        nabywca_kraj = self._podmiot_kraj(root, "Podmiot2", ns)
        if sprzedawca_nip == self.MY_NIP:
            typ = "sprzedaz"
            kontr = Kontrahent(nip=nabywca_nip, nazwa=nabywca_nazwa, kraj=nabywca_kraj)
        elif nabywca_nip == self.MY_NIP:
            typ = "zakup"
            kontr = Kontrahent(nip=sprzedawca_nip, nazwa=sprzedawca_nazwa, kraj=sprzedawca_kraj)
        else:
            typ = "nieznany"
            kontr = Kontrahent(nip="", nazwa="")

        meta["typ"] = typ
        meta["data_wystawienia"] = data_wystawienia
        meta["data_sprzedazy"] = data_sprzedazy
        meta["data_wplywu"] = data_wystawienia if typ == "zakup" else None

        meta["nip_sprzedawcy"] = sprzedawca_nip
        meta["nazwa_sprzedawcy"] = sprzedawca_nazwa
        meta["kraj_sprzedawcy"] = sprzedawca_kraj
        meta["nip_nabywcy"] = nabywca_nip
        meta["nazwa_nabywcy"] = nabywca_nazwa
        meta["kraj_nabywcy"] = nabywca_kraj
        meta["nr_ksef"] = nr_ksef or ""
        meta["numer"] = numer or ""

        meta["rodzaj_faktury"] = rodzaj_faktury
        meta["mpp"] = str(mpp_flag).strip() == "1"
        meta["is_korekta"] = rodzaj_faktury.upper() == "KOR"
        meta["przyczyna_korekty"] = przyczyna_korekty
        meta["nr_fa_korygowanej"] = nr_fa_korygowanej
        meta["data_fa_korygowanej"] = data_fa_korygowanej

        if nr_ksef:
            meta["nr_ksef_source"] = "filename" if nr_ksef_from_filename else "xml"
        else:
            meta["nr_ksef_source"] = "none"

        meta["suma_netto_naglowek"] = str(self._sum_header_by_prefix(root, prefixes=("P_13_",)))
        meta["suma_vat_naglowek"] = str(self._sum_header_by_prefix(root, prefixes=("P_14_",)))
        meta["suma_brutto_naglowek"] = self._find_text_first(
            root,
            [".//fa:P_15"],
            ns,
        )
        if meta["mpp"]:
            meta["procedury"] = sorted(set(meta.get("procedury", []) + ["MPP"]))
        wiersze = root.findall(".//fa:FaWiersz", ns)

        for w in wiersze:
            stan_przed = self._find_text_first(w, ["fa:StanPrzed"], ns)

            if meta["is_korekta"] and not stan_przed:
                continue

            nazwa = self._find_text_first(w, ["fa:P_7"], ns)
            netto_txt = self._find_text_first(
                w,
                ["fa:P_11", "fa:P_11A", "fa:P_9A", "fa:P_9B"],
                ns,
            )
            netto_dec = self._decimal_or_none(netto_txt) or Decimal("0.00")

            vat_txt = self._find_text_first(w, ["fa:P_11Vat"], ns)
            vat_from_xml = self._decimal_or_none(vat_txt)

            stawka_txt = self._find_text_first(w, ["fa:P_12"], ns)
            stawka_norm = self._normalize_stawka(stawka_txt)
            stawka_dec = self._decimal_or_none(stawka_txt)

            procedury = list(meta.get("procedury", []))
            gtu = None

            if stawka_dec is not None:
                stawka = float(stawka_dec)

                if vat_from_xml is not None:
                    vat_dec = vat_from_xml
                else:
                    vat_dec = (netto_dec * stawka_dec / Decimal("100")).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP,
                    )
            else:
                stawka = None
                vat_dec = vat_from_xml if vat_from_xml is not None else Decimal("0.00")

                if stawka_norm in {"ZW", "NP"}:
                    procedury.append(stawka_norm)

                if stawka_norm == "OO":
                    procedury.append("OO")
                    vat_dec = Decimal("0.00")

            kraj_kontrahenta = meta.get("kraj_nabywcy") if typ == "sprzedaz" else meta.get("kraj_sprzedawcy")

            if typ == "sprzedaz" and stawka == 0 and kraj_kontrahenta and kraj_kontrahenta != "PL":
                if kraj_kontrahenta in self.EU_COUNTRIES:
                    procedury.append("WDT")
                else:
                    procedury.append("EXP")

            netto_dec, vat_dec = self._normalize_correction_sign(
                netto_dec,
                vat_dec,
                meta["is_korekta"],
            )

            pozycje.append(
                Pozycja(
                    nazwa=nazwa,
                    netto=float(netto_dec),
                    vat=float(vat_dec),
                    typ=typ,
                    kontrahent=kontr,
                    stawka=stawka,
                    gtu=gtu,
                    procedury=procedury or None,
                )
            )

        meta["liczba_pozycji"] = len(pozycje)
        meta["netto_razem"] = round(sum((p.netto or 0) for p in pozycje), 2)
        meta["vat_razem"] = round(sum((p.vat or 0) for p in pozycje), 2)
        meta["stawki"] = sorted({p.stawka for p in pozycje if p.stawka is not None})

        totals_check = self._build_totals_check(pozycje, meta)
        meta["kontrola_sum"] = totals_check

        input_validation = self._build_input_validation(meta, pozycje)
        meta["walidacja_wejscia"] = input_validation

        if not input_validation["ok"]:
            print(
                "[OSTRZEŻENIE] Walidacja danych wejściowych | "
                f"numer={meta.get('numer')!r} | "
                f"ostrzeżenia={input_validation['warnings']!r}"
            )

        if not totals_check["all_ok"]:
            print(
                "[OSTRZEŻENIE] Niezgodność sum faktury | "
                f"numer={meta.get('numer')!r} | "
                f"netto: pozycje={totals_check['pozycje_netto']} "
                f"vs naglowek={totals_check['naglowek_netto']} | "
                f"vat: pozycje={totals_check['pozycje_vat']} "
                f"vs naglowek={totals_check['naglowek_vat']} | "
                f"brutto: pozycje={totals_check['pozycje_brutto']} "
                f"vs naglowek={totals_check['naglowek_brutto']}"
            )

        return FakturaModel(
            pozycje=pozycje,
            meta=meta,
            nr_ksef=nr_ksef or "",
        )
