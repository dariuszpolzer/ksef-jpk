def crc8(data: bytes) -> int:
    """
    CRC-8 (polynomial 0x07), zgodne z algorytmem KSeF.
    """
    poly = 0x07
    crc = 0x00
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ poly) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def build_ksef_number(nip: str, data_yyyymmdd: str, ident: str) -> str:
    """
    Buduje pełny numer KSeF:
    <NIP>-<DATA>-<IDENT>-<CRC8>
    """
    base = f"{nip}-{data_yyyymmdd}-{ident}"
    checksum = crc8(base.encode("utf-8"))
    return f"{base}-{checksum:02X}"
