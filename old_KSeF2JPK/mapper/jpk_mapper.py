from KSeF2JPK.model.jpk_model import (
    JPKModel,
    SprzedazWiersz,
    SprzedazCtrl,
    ZakupWiersz,
    ZakupCtrl,
)
from KSeF2JPK.model.faktura_model import FakturaModel
from KSeF2JPK.utils.gtu_loader import load_gtu_rules


class JPKMapper:

    def map(self, faktura: FakturaModel) -> JPKModel:
        jpk = JPKModel()

        # ------------------------------------------------------------
        #   ROZDZIEL FAKTURY NA SPRZEDAŻ / ZAKUP
        # ------------------------------------------------------------
        if not faktura.pozycje:
            return jpk

        typ = faktura.pozycje[0].typ  # "sprzedaz" lub "zakup"

        if typ == "sprzedaz":
            self._map_sprzedaz(jpk, faktura)
        else:
            self._map_zakup(jpk, faktura)

        return jpk

    # ------------------------------------------------------------
    #   SPRZEDAŻ
    # ------------------------------------------------------------
    def _map_sprzedaz(self, jpk: JPKModel, faktura: FakturaModel):

        w = SprzedazWiersz()

        # kontrahent = nabywca
        kontr = faktura.pozycje[0].kontrahent
        w.NrKontrahenta = kontr.nip
        w.NazwaKontrahenta = kontr.nazwa
        w.KodKrajuNadaniaTIN = kontr.kraj or "PL"

        # daty
        w.DataWystawienia = faktura.meta.get("data_wystawienia", "")
        w.DataSprzedazy = faktura.meta.get("data_sprzedazy", "")

        # sumy
        w.K_10 = sum(p.netto for p in faktura.pozycje)
        w.K_11 = sum(p.vat for p in faktura.pozycje)

        # GTU
        gtu_rules = load_gtu_rules()
        for p in faktura.pozycje:
            p.gtu = []
            for rule in gtu_rules:
                if rule["nazwa"] in p.nazwa.lower():
                    p.gtu.append(rule["gtu"])

        w.GTU = list({g for p in faktura.pozycje for g in p.gtu})

        jpk.sprzedaz_wiersz.append(w)

        # kontrola
        jpk.sprzedaz_ctrl = SprzedazCtrl(
            LiczbaWierszySprzedazy=1,
            PodatekNalezny=w.K_11
        )

    # ------------------------------------------------------------
    #   ZAKUP
    # ------------------------------------------------------------
    def _map_zakup(self, jpk: JPKModel, faktura: FakturaModel):

        w = ZakupWiersz()

        # kontrahent = sprzedawca
        kontr = faktura.pozycje[0].kontrahent
        w.NrDostawcy = kontr.nip
        w.NazwaDostawcy = kontr.nazwa
        w.KodKrajuNadaniaTIN = kontr.kraj or "PL"

        # daty
        w.DataWplywu = faktura.meta.get("data_wystawienia", "")
        w.DataZakupu = faktura.meta.get("data_sprzedazy", "")

        # sumy zakupowe
        # K_40 – netto
        # K_41 – VAT naliczony
        w.K_40 = sum(p.netto for p in faktura.pozycje)
        w.K_41 = sum(p.vat for p in faktura.pozycje)

        jpk.zakup_wiersz.append(w)

        # kontrola
        jpk.zakup_ctrl = ZakupCtrl(
            LiczbaWierszyZakupow=1,
            PodatekNaliczony=w.K_41
        )
