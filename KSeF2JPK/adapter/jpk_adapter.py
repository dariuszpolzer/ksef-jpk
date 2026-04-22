from KSeF2JPK.model.jpk_model import (
    JPKModel,
    SprzedazWiersz,
    ZakupWiersz,
    SprzedazCtrl,
    ZakupCtrl,
)


def dict_to_jpk_model(jpk_dict: dict) -> JPKModel:
    jpk = JPKModel()

    # ---------------- Nagłówek ----------------
    nag = jpk_dict.get("Naglowek", {})
    jpk.data_wytworzenia = nag.get("DataWytworzeniaJPK", "")
    jpk.data_od = nag.get("DataOd", "")
    jpk.data_do = nag.get("DataDo", "")
    jpk.kod_urzedu = nag.get("KodUrzedu", "")

    # ---------------- Podmiot ----------------
    pod = jpk_dict.get("Podmiot1", {})
    jpk.nip = pod.get("NIP") or pod.get("nip") or ""
    jpk.nazwa = pod.get("Nazwa") or pod.get("PelnaNazwa") or pod.get("nazwa") or ""
    jpk.data_urodzenia = pod.get("DataUrodzenia") or pod.get("data_urodzenia") or ""
    jpk.email = pod.get("Email") or pod.get("email") or ""
    jpk.telefon = pod.get("Telefon") or pod.get("telefon") or ""

    # ---------------- Deklaracja ----------------
    poz = jpk_dict.get("Deklaracja", {}).get("PozycjeSzczegolowe", {})
    for pole in [
        "P_10", "P_11", "P_12", "P_13", "P_14", "P_15", "P_16", "P_17", "P_18",
        "P_19", "P_20", "P_21", "P_22", "P_23", "P_24", "P_25", "P_26", "P_27",
        "P_28", "P_29", "P_30", "P_31", "P_32", "P_33", "P_34", "P_35", "P_36",
        "P_37", "P_38", "P_39", "P_40", "P_41", "P_42", "P_43", "P_44", "P_45",
        "P_46", "P_47", "P_48", "P_49", "P_50", "P_51", "P_52", "P_53", "P_54",
        "P_55", "P_56", "P_57", "P_58", "P_59", "P_60", "P_61", "P_62", "P_63",
        "P_64", "P_65", "P_66", "P_67", "P_68", "P_69", "P_ORDZU",
    ]:
        if pole in poz:
            setattr(jpk.deklaracja, pole, poz.get(pole))

    # ---------------- Ewidencja ----------------
    
    e = jpk_dict.get("Ewidencja", {})

    # Sprzedaż
    for w in e.get("SprzedazWiersz", []):
        sw = SprzedazWiersz(
            LpSprzedazy=w["LpSprzedazy"],
            NrKontrahenta=w["NrKontrahenta"],
            NazwaKontrahenta=w["NazwaKontrahenta"],
            DowodSprzedazy=w["DowodSprzedazy"],
            DataWystawienia=w["DataWystawienia"],
            DataSprzedazy=w["DataSprzedazy"],
            NrKSeF=w.get("NrKSeF", ""),
            K_19=w.get("K_19", 0),
            K_20=w.get("K_20", 0),
            K_21=w.get("K_21", 0),
            K_22=w.get("K_22", 0),
            K_23=w.get("K_23", 0),
            K_24=w.get("K_24", 0),
            K_27=w.get("K_27", 0),
            K_28=w.get("K_28", 0),
        )

        # pola opcjonalne / procedury
        for attr in ["GTU", "WDT", "Eksport", "OO", "MPP", "Marza", "SW", "EE", "TP", "OFF"]:
            if attr in w:
                setattr(sw, attr, w[attr])

        jpk.sprzedaz_wiersz.append(sw)

    # Zakup
    for w in e.get("ZakupWiersz", []):
        zw = ZakupWiersz(
            LpZakupu=w["LpZakupu"],
            NrDostawcy=w["NrDostawcy"],
            NazwaDostawcy=w["NazwaDostawcy"],
            DowodZakupu=w["DowodZakupu"],
            DataZakupu=w["DataZakupu"],
            DataWplywu=w["DataWplywu"],
            NrKSeF=w.get("NrKSeF", ""),
            K_42=w.get("K_42", 0),
            K_43=w.get("K_43", 0),
            K_44=w.get("K_44", 0),
            K_45=w.get("K_45", 0),
            K_46=w.get("K_46", 0),
            K_47=w.get("K_47", 0),
        )

        for attr in ["GTU", "IMP", "MPP", "OO", "VAT_RR", "OFF"]:
            if attr in w:
                setattr(zw, attr, w[attr])

        jpk.zakup_wiersz.append(zw)

    # ---------------- Ctrl ----------------
    sc = e.get("SprzedazCtrl")
    if sc:
        jpk.sprzedaz_ctrl = SprzedazCtrl(
            LiczbaWierszySprzedazy=sc.get("LiczbaWierszySprzedazy", 0),
            PodatekNalezny=sc.get("PodatekNalezny", 0),
        )

    zc = e.get("ZakupCtrl")
    if zc:
        jpk.zakup_ctrl = ZakupCtrl(
            LiczbaWierszyZakupow=zc.get("LiczbaWierszyZakupow", 0),
            PodatekNaliczony=zc.get("PodatekNaliczony", 0),
        )

    return jpk