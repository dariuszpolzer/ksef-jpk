import os
import json
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from ksef2jpk.model.faktura_model import FakturaModel, Pozycja, Kontrahent
from ksef2jpk.utils.ksef_number import extract_ksef_number_from_filename


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "config.json"))


with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)


class KSeFParser:
    MY_NIP = CONFIG["podmiot"]["nip"]

    def _text(self, el) -> str:
        if el is None or el.text is None:
            return ""
        return el.text.strip()

    def _decimal_or_none(self, text: str | None):
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

    def _find_text_first(self, root, paths, ns) -> str:
        for path in paths:
            try:
                el = root.find(path, ns)
            except SyntaxError:
                continue
            txt = self._text(el)
            if txt:
                return txt
        return ""

    def _podmiot_nazwa(self, root, podmiot_tag: str, ns) -> str:
        candidates = [
            f".//fa:{podmiot_tag}/fa:DaneIdentyfikacyjne/fa:Nazwa",
            f".//fa:{podmiot_tag}/fa:DaneIdentyfikacyjne/fa:NazwaPelna",
            f".//fa:{podmiot_tag}/fa:DaneIdentyfikacyjne/fa:PelnaNazwa",
            f".//fa:{podmiot_tag}/fa:DaneIdentyfikacyjne/fa:ImiePierwsze",
        ]
        return self._find_text_first(root, candidates, ns)

    def _normalize_stawka(self, raw: str) -> str:
        return (raw or "").strip().upper()

    def _is_close(self, a: Decimal, b: Decimal, tolerance: Decimal = Decimal("0.01")) -> bool:
        return abs(a - b) <= tolerance

    def _build_totals_check(self, pozycje, meta):
        netto_poz = sum((Decimal(str(p.netto)) for p in pozycje), Decimal("0.00"))
        vat_poz = sum((Decimal(str(p.vat)) for p in pozycje), Decimal("0.00"))
        brutto_poz = netto_poz + vat_poz

        netto_nag = self._decimal_or_none(meta.get("suma_netto_naglowek_23")) or Decimal("0.00")
        vat_nag = self._decimal_or_none(meta.get("suma_vat_naglowek_23")) or Decimal("0.00")
        brutto_nag = self._decimal_or_none(meta.get("suma_brutto_naglowek")) or Decimal("0.00")

        result = {
            "pozycje_netto": float(netto_poz),
            "pozycje_vat": float(vat_poz),
            "pozycje_brutto": float(brutto_poz),
            "naglowek_netto": float(netto_nag),
            "naglowek_vat": float(vat_nag),
            "naglowek_brutto": float(brutto_nag),
            "netto_ok": self._is_close(netto_poz, netto_nag),
            "vat_ok": self._is_close(vat_poz, vat_nag),
            "brutto_ok": self._is_close(brutto_poz, brutto_nag),
        }
        result["all_ok"] = result["netto_ok"] and result["vat_ok"] and result["brutto_ok"]
        return result

    def parse(self, xml_path: str) -> FakturaModel:
        meta = {}
        pozycje = []

        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = self._get_ns(root)

        filename = os.path.basename(xml_path)

        data_wystawienia = self._find_text_first(root, [
            ".//fa:Fa/fa:P_1",
            ".//fa:P_1",
        ], ns)

        numer = self._find_text_first(root, [
            ".//fa:Fa/fa:P_2",
            ".//fa:P_2",
        ], ns)

        data_sprzedazy = self._find_text_first(root, [
            ".//fa:Fa/fa:P_6",
            ".//fa:P_6",
            ".//fa:Fa/fa:OkresFa/fa:P_6_Do",
            ".//fa:OkresFa/fa:P_6_Do",
            ".//fa:Fa/fa:OkresFa/fa:P_6_Od",
            ".//fa:OkresFa/fa:P_6_Od",
        ], ns)

        nr_ksef = self._find_text_first(root, [
            ".//fa:NrKSeF",
        ], ns)

        nr_ksef_from_filename = ""
        if not nr_ksef:
            nr_ksef_from_filename = extract_ksef_number_from_filename(filename)
            if nr_ksef_from_filename:
                nr_ksef = nr_ksef_from_filename

        sprzedawca_nip = self._find_text_first(root, [
            ".//fa:Podmiot1/fa:DaneIdentyfikacyjne/fa:NIP",
            ".//fa:Podmiot1//fa:NIP",
        ], ns)

        sprzedawca_nazwa = self._podmiot_nazwa(root, "Podmiot1", ns)

        nabywca_nip = self._find_text_first(root, [
            ".//fa:Podmiot2/fa:DaneIdentyfikacyjne/fa:NIP",
            ".//fa:Podmiot2//fa:NIP",
        ], ns)

        nabywca_nazwa = self._podmiot_nazwa(root, "Podmiot2", ns)

        if sprzedawca_nip == self.MY_NIP:
            typ = "sprzedaz"
            kontr = Kontrahent(nip=nabywca_nip, nazwa=nabywca_nazwa)
        elif nabywca_nip == self.MY_NIP:
            typ = "zakup"
            kontr = Kontrahent(nip=sprzedawca_nip, nazwa=sprzedawca_nazwa)
        else:
            typ = "nieznany"
            kontr = Kontrahent(nip="", nazwa="")

        meta["typ"] = typ
        meta["data_wystawienia"] = data_wystawienia
        meta["data_sprzedazy"] = data_sprzedazy
        meta["data_wplywu"] = data_wystawienia if typ == "zakup" else None

        meta["nip_sprzedawcy"] = sprzedawca_nip
        meta["nazwa_sprzedawcy"] = sprzedawca_nazwa
        meta["nip_nabywcy"] = nabywca_nip
        meta["nazwa_nabywcy"] = nabywca_nazwa

        meta["nr_ksef"] = nr_ksef or ""
        meta["numer"] = numer or ""

        if nr_ksef:
            meta["nr_ksef_source"] = "filename" if nr_ksef_from_filename else "xml"
        else:
            meta["nr_ksef_source"] = "none"

        meta["suma_netto_naglowek_23"] = self._find_text_first(root, [".//fa:P_13_1"], ns)
        meta["suma_vat_naglowek_23"] = self._find_text_first(root, [".//fa:P_14_1"], ns)
        meta["suma_brutto_naglowek"] = self._find_text_first(root, [".//fa:P_15"], ns)

        wiersze = root.findall(".//fa:FaWiersz", ns)

        for w in wiersze:
            nazwa = self._find_text_first(w, ["fa:P_7"], ns)

            netto_txt = self._find_text_first(w, [
                "fa:P_11",
                "fa:P_11A",
                "fa:P_9A",
                "fa:P_9B",
            ], ns)
            netto_dec = self._decimal_or_none(netto_txt) or Decimal("0.00")

            vat_txt = self._find_text_first(w, [
                "fa:P_11Vat",
            ], ns)
            vat_from_xml = self._decimal_or_none(vat_txt)

            stawka_txt = self._find_text_first(w, ["fa:P_12"], ns)
            stawka_norm = self._normalize_stawka(stawka_txt)
            stawka_dec = self._decimal_or_none(stawka_txt)

            procedury = []
            gtu = None

            if stawka_dec is not None:
                stawka = float(stawka_dec)

                if vat_from_xml is not None:
                    vat_dec = vat_from_xml
                else:
                    vat_dec = (netto_dec * stawka_dec / Decimal("100")).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )
            else:
                stawka = None
                vat_dec = vat_from_xml if vat_from_xml is not None else Decimal("0.00")

                if stawka_norm in {"ZW", "NP", "OO"}:
                    procedury.append(stawka_norm)

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

        stawki = sorted({p.stawka for p in pozycje if p.stawka is not None})
        meta["stawki"] = stawki

        totals_check = self._build_totals_check(pozycje, meta)
        meta["kontrola_sum"] = totals_check

        if not totals_check["all_ok"]:
            print(
                "[OSTRZEŻENIE] Niezgodność sum faktury | "
                f"numer={meta.get('numer')!r} | "
                f"netto: pozycje={totals_check['pozycje_netto']} vs naglowek={totals_check['naglowek_netto']} | "
                f"vat: pozycje={totals_check['pozycje_vat']} vs naglowek={totals_check['naglowek_vat']} | "
                f"brutto: pozycje={totals_check['pozycje_brutto']} vs naglowek={totals_check['naglowek_brutto']}"
            )

        return FakturaModel(
            pozycje=pozycje,
            meta=meta,
            nr_ksef=nr_ksef or ""
        )


# import os
# import json
# import xml.etree.ElementTree as ET
# from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# from ksef2jpk.model.faktura_model import FakturaModel, Pozycja, Kontrahent
# from ksef2jpk.utils.ksef_number import extract_ksef_number_from_filename

# # Ścieżka do katalogu, w którym znajduje się ten plik
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# CONFIG_PATH = os.path.join(BASE_DIR, "..", "..", "config.json")


# # Wczytanie config.json
# with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    # CONFIG = json.load(f)

# # Pobranie NIP z config.json
# MY_NIP = CONFIG["podmiot"]["nip"]


# class KSeFParser:
    # def __init__(self, my_nip: str):
        # self.MY_NIP = my_nip

    # def _text(self, el) -> str:
        # if el is None or el.text is None:
            # return ""
        # return el.text.strip()

    # def _decimal_or_none(self, text: str | None):
        # if text is None:
            # return None
        # text = text.strip().replace(",", ".")
        # if not text:
            # return None
        # try:
            # return Decimal(text)
        # except InvalidOperation:
            # return None

    # def _get_ns(self, root):
        # if root.tag.startswith("{"):
            # uri = root.tag.split("}")[0][1:]
            # return {"fa": uri}
        # return {}


    # def _text(self, el) -> str:
        # if el is None or el.text is None:
            # return ""
        # return el.text.strip()

    # def _decimal_or_none(self, text: str | None):
        # if text is None:
            # return None
        # text = text.strip().replace(",", ".")
        # if not text:
            # return None
        # try:
            # return Decimal(text)
        # except InvalidOperation:
            # return None

    # def _get_ns(self, root):
        # if root.tag.startswith("{"):
            # uri = root.tag.split("}")[0][1:]
            # return {"fa": uri}
        # return {}

    # def _find_text_first(self, root, paths, ns) -> str:
        # for path in paths:
            # try:
                # el = root.find(path, ns)
            # except SyntaxError:
                # continue
            # txt = self._text(el)
            # if txt:
                # return txt
        # return ""

    # def _podmiot_nazwa(self, root, podmiot_tag: str, ns) -> str:
        # candidates = [
            # f".//fa:{podmiot_tag}/fa:DaneIdentyfikacyjne/fa:Nazwa",
            # f".//fa:{podmiot_tag}/fa:DaneIdentyfikacyjne/fa:NazwaPelna",
            # f".//fa:{podmiot_tag}/fa:DaneIdentyfikacyjne/fa:PelnaNazwa",
            # f".//fa:{podmiot_tag}/fa:DaneIdentyfikacyjne/fa:ImiePierwsze",
        # ]
        # return self._find_text_first(root, candidates, ns)

    # def _normalize_stawka(self, raw: str) -> str:
        # return (raw or "").strip().upper()

    # def _is_close(self, a: Decimal, b: Decimal, tolerance: Decimal = Decimal("0.01")) -> bool:
        # return abs(a - b) <= tolerance

    # def _build_totals_check(self, pozycje, meta):
        # netto_poz = sum((Decimal(str(p.netto)) for p in pozycje), Decimal("0.00"))
        # vat_poz = sum((Decimal(str(p.vat)) for p in pozycje), Decimal("0.00"))
        # brutto_poz = netto_poz + vat_poz

        # netto_nag = self._decimal_or_none(meta.get("suma_netto_naglowek_23")) or Decimal("0.00")
        # vat_nag = self._decimal_or_none(meta.get("suma_vat_naglowek_23")) or Decimal("0.00")
        # brutto_nag = self._decimal_or_none(meta.get("suma_brutto_naglowek")) or Decimal("0.00")

        # result = {
            # "pozycje_netto": float(netto_poz),
            # "pozycje_vat": float(vat_poz),
            # "pozycje_brutto": float(brutto_poz),
            # "naglowek_netto": float(netto_nag),
            # "naglowek_vat": float(vat_nag),
            # "naglowek_brutto": float(brutto_nag),
            # "netto_ok": self._is_close(netto_poz, netto_nag),
            # "vat_ok": self._is_close(vat_poz, vat_nag),
            # "brutto_ok": self._is_close(brutto_poz, brutto_nag),
        # }
        # result["all_ok"] = result["netto_ok"] and result["vat_ok"] and result["brutto_ok"]
        # return result

    # def parse(self, xml_path: str) -> FakturaModel:
        # meta = {}
        # pozycje = []

        # tree = ET.parse(xml_path)
        # root = tree.getroot()
        # ns = self._get_ns(root)

        # filename = os.path.basename(xml_path)

        # # -------------------------
        # # Nagłówek faktury
        # # -------------------------
        # data_wystawienia = self._find_text_first(root, [
            # ".//fa:Fa/fa:P_1",
            # ".//fa:P_1",
        # ], ns)

        # numer = self._find_text_first(root, [
            # ".//fa:Fa/fa:P_2",
            # ".//fa:P_2",
        # ], ns)

        # data_sprzedazy = self._find_text_first(root, [
            # ".//fa:Fa/fa:P_6",
            # ".//fa:P_6",
            # ".//fa:Fa/fa:OkresFa/fa:P_6_Do",
            # ".//fa:OkresFa/fa:P_6_Do",
            # ".//fa:Fa/fa:OkresFa/fa:P_6_Od",
            # ".//fa:OkresFa/fa:P_6_Od",
        # ], ns)

        # # -------------------------
        # # NrKSeF – z XML albo z nazwy pliku
        # # -------------------------
        # nr_ksef = self._find_text_first(root, [
            # ".//fa:NrKSeF",
        # ], ns)

        # nr_ksef_from_filename = ""
        # if not nr_ksef:
            # nr_ksef_from_filename = extract_ksef_number_from_filename(filename)
            # if nr_ksef_from_filename:
                # nr_ksef = nr_ksef_from_filename

        # # -------------------------
        # # Podmioty
        # # -------------------------
        # sprzedawca_nip = self._find_text_first(root, [
            # ".//fa:Podmiot1/fa:DaneIdentyfikacyjne/fa:NIP",
            # ".//fa:Podmiot1//fa:NIP",
        # ], ns)

        # sprzedawca_nazwa = self._podmiot_nazwa(root, "Podmiot1", ns)

        # nabywca_nip = self._find_text_first(root, [
            # ".//fa:Podmiot2/fa:DaneIdentyfikacyjne/fa:NIP",
            # ".//fa:Podmiot2//fa:NIP",
        # ], ns)

        # nabywca_nazwa = self._podmiot_nazwa(root, "Podmiot2", ns)

        # if sprzedawca_nip == self.MY_NIP:
            # typ = "sprzedaz"
            # kontr = Kontrahent(nip=nabywca_nip, nazwa=nabywca_nazwa)
        # elif nabywca_nip == self.MY_NIP:
            # typ = "zakup"
            # kontr = Kontrahent(nip=sprzedawca_nip, nazwa=sprzedawca_nazwa)
        # else:
            # typ = "nieznany"
            # kontr = Kontrahent(nip="", nazwa="")

        # # -------------------------
        # # Rozpoznanie korekty – tylko sygnał, bez księgowania
        # # -------------------------
        # rodzaj_faktury = self._find_text_first(root, [
            # ".//fa:RodzajFaktury",
        # ], ns)

        # przyczyna_korekty = self._find_text_first(root, [
            # ".//fa:PrzyczynaKorekty",
        # ], ns)

        # nr_fa_korygowanej = self._find_text_first(root, [
            # ".//fa:DaneFaKorygowanej/fa:NrFaKorygowanej",
        # ], ns)

        # data_fa_korygowanej = self._find_text_first(root, [
            # ".//fa:DaneFaKorygowanej/fa:DataWystFaKorygowanej",
        # ], ns)

        # nr_ksef_korygowanej_flag = self._find_text_first(root, [
            # ".//fa:DaneFaKorygowanej/fa:NrKSeFN",
        # ], ns)

        # is_korekta = (rodzaj_faktury or "").strip().upper() == "KOR"

        # meta["typ"] = typ
        # meta["data_wystawienia"] = data_wystawienia
        # meta["data_sprzedazy"] = data_sprzedazy
        # meta["data_wplywu"] = data_wystawienia if typ == "zakup" else None

        # meta["nip_sprzedawcy"] = sprzedawca_nip
        # meta["nazwa_sprzedawcy"] = sprzedawca_nazwa
        # meta["nip_nabywcy"] = nabywca_nip
        # meta["nazwa_nabywcy"] = nabywca_nazwa

        # meta["nr_ksef"] = nr_ksef or ""
        # meta["numer"] = numer or ""

        # if nr_ksef:
            # meta["nr_ksef_source"] = "filename" if nr_ksef_from_filename else "xml"
        # else:
            # meta["nr_ksef_source"] = "none"

        # meta["rodzaj_faktury"] = rodzaj_faktury
        # meta["is_korekta"] = is_korekta
        # meta["przyczyna_korekty"] = przyczyna_korekty
        # meta["nr_fa_korygowanej"] = nr_fa_korygowanej
        # meta["data_fa_korygowanej"] = data_fa_korygowanej
        # meta["nr_ksef_korygowanej_flag"] = nr_ksef_korygowanej_flag

        # # -------------------------
        # # Sumy nagłówkowe pomocniczo
        # # -------------------------
        # meta["suma_netto_naglowek_23"] = self._find_text_first(root, [".//fa:P_13_1"], ns)
        # meta["suma_vat_naglowek_23"] = self._find_text_first(root, [".//fa:P_14_1"], ns)
        # meta["suma_brutto_naglowek"] = self._find_text_first(root, [".//fa:P_15"], ns)

        # # -------------------------
        # # Wiersze faktury
        # # Bez specjalnego liczenia korekt — tylko zwykły odczyt
        # # -------------------------
        # wiersze = root.findall(".//fa:FaWiersz", ns)

        # for w in wiersze:
            # nazwa = self._find_text_first(w, ["fa:P_7"], ns)

            # netto_txt = self._find_text_first(w, [
                # "fa:P_11",
                # "fa:P_11A",
                # "fa:P_9A",
                # "fa:P_9B",
            # ], ns)
            # netto_dec = self._decimal_or_none(netto_txt) or Decimal("0.00")

            # vat_txt = self._find_text_first(w, [
                # "fa:P_11Vat",
            # ], ns)
            # vat_from_xml = self._decimal_or_none(vat_txt)

            # stawka_txt = self._find_text_first(w, ["fa:P_12"], ns)
            # stawka_norm = self._normalize_stawka(stawka_txt)
            # stawka_dec = self._decimal_or_none(stawka_txt)

            # procedury = []
            # gtu = None

            # if stawka_dec is not None:
                # stawka = float(stawka_dec)

                # if vat_from_xml is not None:
                    # vat_dec = vat_from_xml
                # else:
                    # vat_dec = (netto_dec * stawka_dec / Decimal("100")).quantize(
                        # Decimal("0.01"),
                        # rounding=ROUND_HALF_UP
                    # )
            # else:
                # stawka = None
                # vat_dec = vat_from_xml if vat_from_xml is not None else Decimal("0.00")

                # if stawka_norm in {"ZW", "NP", "OO"}:
                    # procedury.append(stawka_norm)

            # pozycje.append(
                # Pozycja(
                    # nazwa=nazwa,
                    # netto=float(netto_dec),
                    # vat=float(vat_dec),
                    # typ=typ,
                    # kontrahent=kontr,
                    # stawka=stawka,
                    # gtu=gtu,
                    # procedury=procedury or None,
                # )
            # )

        # # -------------------------
        # # Agregaty pomocnicze
        # # -------------------------
        # meta["liczba_pozycji"] = len(pozycje)
        # meta["netto_razem"] = round(sum((p.netto or 0) for p in pozycje), 2)
        # meta["vat_razem"] = round(sum((p.vat or 0) for p in pozycje), 2)

        # stawki = sorted({p.stawka for p in pozycje if p.stawka is not None})
        # meta["stawki"] = stawki

        # totals_check = self._build_totals_check(pozycje, meta)
        # meta["kontrola_sum"] = totals_check

        # if not totals_check["all_ok"]:
            # print(
                # "[OSTRZEŻENIE] Niezgodność sum faktury | "
                # f"numer={meta.get('numer')!r} | "
                # f"netto: pozycje={totals_check['pozycje_netto']} vs naglowek={totals_check['naglowek_netto']} | "
                # f"vat: pozycje={totals_check['pozycje_vat']} vs naglowek={totals_check['naglowek_vat']} | "
                # f"brutto: pozycje={totals_check['pozycje_brutto']} vs naglowek={totals_check['naglowek_brutto']}"
            # )

        # return FakturaModel(
            # pozycje=pozycje,
            # meta=meta,
            # nr_ksef=nr_ksef or ""
        # )





# # import xml.etree.ElementTree as ET
# # from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# # from ksef2jpk.model.faktura_model import FakturaModel, Pozycja, Kontrahent


# # class KSeFParser:
    # # MY_NIP = "6791444505"

    # # def _text(self, el) -> str:
        # # if el is None or el.text is None:
            # # return ""
        # # return el.text.strip()

    # # def _decimal_or_none(self, text: str | None):
        # # if text is None:
            # # return None
        # # text = text.strip().replace(",", ".")
        # # if not text:
            # # return None
        # # try:
            # # return Decimal(text)
        # # except InvalidOperation:
            # # return None

    # # def _get_ns(self, root):
        # # if root.tag.startswith("{"):
            # # uri = root.tag.split("}")[0][1:]
            # # return {"fa": uri}
        # # return {}

    # # def _find_text_first(self, root, paths, ns) -> str:
        # # for path in paths:
            # # try:
                # # el = root.find(path, ns)
            # # except SyntaxError:
                # # continue
            # # txt = self._text(el)
            # # if txt:
                # # return txt
        # # return ""

    # # def _podmiot_nazwa(self, root, podmiot_tag: str, ns) -> str:
        # # candidates = [
            # # f".//fa:{podmiot_tag}/fa:DaneIdentyfikacyjne/fa:Nazwa",
            # # f".//fa:{podmiot_tag}/fa:DaneIdentyfikacyjne/fa:NazwaPelna",
            # # f".//fa:{podmiot_tag}/fa:DaneIdentyfikacyjne/fa:PelnaNazwa",
            # # f".//fa:{podmiot_tag}/fa:DaneIdentyfikacyjne/fa:ImiePierwsze",
        # # ]
        # # return self._find_text_first(root, candidates, ns)

    # # def _normalize_stawka(self, raw: str) -> str:
        # # return (raw or "").strip().upper()

    # # def _is_close(self, a: Decimal, b: Decimal, tolerance: Decimal = Decimal("0.01")) -> bool:
        # # return abs(a - b) <= tolerance

    # # def _build_totals_check(self, pozycje, meta):
        # # netto_poz = sum((Decimal(str(p.netto)) for p in pozycje), Decimal("0.00"))
        # # vat_poz = sum((Decimal(str(p.vat)) for p in pozycje), Decimal("0.00"))
        # # brutto_poz = netto_poz + vat_poz

        # # netto_nag = self._decimal_or_none(meta.get("suma_netto_naglowek_23")) or Decimal("0.00")
        # # vat_nag = self._decimal_or_none(meta.get("suma_vat_naglowek_23")) or Decimal("0.00")
        # # brutto_nag = self._decimal_or_none(meta.get("suma_brutto_naglowek")) or Decimal("0.00")

        # # result = {
            # # "pozycje_netto": float(netto_poz),
            # # "pozycje_vat": float(vat_poz),
            # # "pozycje_brutto": float(brutto_poz),
            # # "naglowek_netto": float(netto_nag),
            # # "naglowek_vat": float(vat_nag),
            # # "naglowek_brutto": float(brutto_nag),
            # # "netto_ok": self._is_close(netto_poz, netto_nag),
            # # "vat_ok": self._is_close(vat_poz, vat_nag),
            # # "brutto_ok": self._is_close(brutto_poz, brutto_nag),
        # # }
        # # result["all_ok"] = result["netto_ok"] and result["vat_ok"] and result["brutto_ok"]
        # # return result

    # # def parse(self, xml_path: str) -> FakturaModel:
        # # meta = {}
        # # pozycje = []

        # # tree = ET.parse(xml_path)
        # # root = tree.getroot()
        # # ns = self._get_ns(root)

        # # # -------------------------
        # # # Nagłówek faktury
        # # # -------------------------
        # # data_wystawienia = self._find_text_first(root, [
            # # ".//fa:Fa/fa:P_1",
            # # ".//fa:P_1",
        # # ], ns)

        # # numer = self._find_text_first(root, [
            # # ".//fa:Fa/fa:P_2",
            # # ".//fa:P_2",
        # # ], ns)

        # # # Najpierw zwykłe P_6, potem faktura okresowa
        # # data_sprzedazy = self._find_text_first(root, [
            # # ".//fa:Fa/fa:P_6",
            # # ".//fa:P_6",
            # # ".//fa:Fa/fa:OkresFa/fa:P_6_Do",
            # # ".//fa:OkresFa/fa:P_6_Do",
            # # ".//fa:Fa/fa:OkresFa/fa:P_6_Od",
            # # ".//fa:OkresFa/fa:P_6_Od",
        # # ], ns)

        # # nr_ksef = self._find_text_first(root, [
            # # ".//fa:NrKSeF",
        # # ], ns)

        # # # -------------------------
        # # # Podmioty
        # # # -------------------------
        # # sprzedawca_nip = self._find_text_first(root, [
            # # ".//fa:Podmiot1/fa:DaneIdentyfikacyjne/fa:NIP",
            # # ".//fa:Podmiot1//fa:NIP",
        # # ], ns)

        # # sprzedawca_nazwa = self._podmiot_nazwa(root, "Podmiot1", ns)

        # # nabywca_nip = self._find_text_first(root, [
            # # ".//fa:Podmiot2/fa:DaneIdentyfikacyjne/fa:NIP",
            # # ".//fa:Podmiot2//fa:NIP",
        # # ], ns)

        # # nabywca_nazwa = self._podmiot_nazwa(root, "Podmiot2", ns)

        # # if sprzedawca_nip == self.MY_NIP:
            # # typ = "sprzedaz"
            # # kontr = Kontrahent(nip=nabywca_nip, nazwa=nabywca_nazwa)
        # # elif nabywca_nip == self.MY_NIP:
            # # typ = "zakup"
            # # kontr = Kontrahent(nip=sprzedawca_nip, nazwa=sprzedawca_nazwa)
        # # else:
            # # typ = "nieznany"
            # # kontr = Kontrahent(nip="", nazwa="")

        # # meta["typ"] = typ
        # # meta["data_wystawienia"] = data_wystawienia
        # # meta["data_sprzedazy"] = data_sprzedazy
        # # meta["data_wplywu"] = data_wystawienia if typ == "zakup" else None

        # # meta["nip_sprzedawcy"] = sprzedawca_nip
        # # meta["nazwa_sprzedawcy"] = sprzedawca_nazwa
        # # meta["nip_nabywcy"] = nabywca_nip
        # # meta["nazwa_nabywcy"] = nabywca_nazwa

        # # meta["nr_ksef"] = nr_ksef or ""
        # # meta["numer"] = numer or ""

        # # # -------------------------
        # # # Sumy nagłówkowe pomocniczo
        # # # Na razie głównie pod stawkę 23%; przy dalszym rozwoju
        # # # można rozszerzyć o P_13_2, P_14_2 itd.
        # # # -------------------------
        # # meta["suma_netto_naglowek_23"] = self._find_text_first(root, [".//fa:P_13_1"], ns)
        # # meta["suma_vat_naglowek_23"] = self._find_text_first(root, [".//fa:P_14_1"], ns)
        # # meta["suma_brutto_naglowek"] = self._find_text_first(root, [".//fa:P_15"], ns)

        # # # -------------------------
        # # # Wiersze faktury
        # # # -------------------------
        # # wiersze = root.findall(".//fa:FaWiersz", ns)

        # # for w in wiersze:
            # # nazwa = self._find_text_first(w, ["fa:P_7"], ns)

            # # # Netto:
            # # # 1) P_11
            # # # 2) P_11A
            # # # 3) P_9A / P_9B jako fallback awaryjny
            # # netto_txt = self._find_text_first(w, [
                # # "fa:P_11",
                # # "fa:P_11A",
                # # "fa:P_9A",
                # # "fa:P_9B",
            # # ], ns)
            # # netto_dec = self._decimal_or_none(netto_txt) or Decimal("0.00")

            # # # VAT pozycji - jeśli system źródłowy podał, używamy tej wartości
            # # vat_txt = self._find_text_first(w, [
                # # "fa:P_11Vat",
            # # ], ns)
            # # vat_from_xml = self._decimal_or_none(vat_txt)

            # # stawka_txt = self._find_text_first(w, ["fa:P_12"], ns)
            # # stawka_norm = self._normalize_stawka(stawka_txt)
            # # stawka_dec = self._decimal_or_none(stawka_txt)

            # # procedury = []
            # # gtu = None

            # # if stawka_dec is not None:
                # # stawka = float(stawka_dec)

                # # if vat_from_xml is not None:
                    # # vat_dec = vat_from_xml
                # # else:
                    # # vat_dec = (netto_dec * stawka_dec / Decimal("100")).quantize(
                        # # Decimal("0.01"),
                        # # rounding=ROUND_HALF_UP
                    # # )
            # # else:
                # # # stawki typu ZW, NP, OO
                # # stawka = None
                # # vat_dec = vat_from_xml if vat_from_xml is not None else Decimal("0.00")

                # # if stawka_norm in {"ZW", "NP", "OO"}:
                    # # procedury.append(stawka_norm)

            # # pozycje.append(
                # # Pozycja(
                    # # nazwa=nazwa,
                    # # netto=float(netto_dec),
                    # # vat=float(vat_dec),
                    # # typ=typ,
                    # # kontrahent=kontr,
                    # # stawka=stawka,
                    # # gtu=gtu,
                    # # procedury=procedury or None,
                # # )
            # # )

        # # # -------------------------
        # # # Agregaty pomocnicze
        # # # -------------------------
        # # meta["liczba_pozycji"] = len(pozycje)
        # # meta["netto_razem"] = round(sum((p.netto or 0) for p in pozycje), 2)
        # # meta["vat_razem"] = round(sum((p.vat or 0) for p in pozycje), 2)

        # # stawki = sorted({p.stawka for p in pozycje if p.stawka is not None})
        # # meta["stawki"] = stawki

        # # totals_check = self._build_totals_check(pozycje, meta)
        # # meta["kontrola_sum"] = totals_check

        # # if not totals_check["all_ok"]:
            # # print(
                # # "[OSTRZEŻENIE] Niezgodność sum faktury | "
                # # f"numer={meta.get('numer')!r} | "
                # # f"netto: pozycje={totals_check['pozycje_netto']} vs naglowek={totals_check['naglowek_netto']} | "
                # # f"vat: pozycje={totals_check['pozycje_vat']} vs naglowek={totals_check['naglowek_vat']} | "
                # # f"brutto: pozycje={totals_check['pozycje_brutto']} vs naglowek={totals_check['naglowek_brutto']}"
            # # )

        # # return FakturaModel(
            # # pozycje=pozycje,
            # # meta=meta,
            # # nr_ksef=nr_ksef or ""
        # # )