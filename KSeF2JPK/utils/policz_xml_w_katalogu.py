import os

def policz_xml_w_katalogu(folder_path: str) -> int:
    """
    Zlicza pliki *.xml w podanym katalogu (bez podfolderów).

    :param folder_path: ścieżka do katalogu
    :return: liczba plików XML
    """
    if not os.path.isdir(folder_path):
        return 0

    licznik = 0
    for nazwa in os.listdir(folder_path):
        if nazwa.lower().endswith(".xml"):
            licznik += 1

    return licznik
