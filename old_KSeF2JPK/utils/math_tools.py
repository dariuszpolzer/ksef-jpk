def safe_float(value):
    try:
        return float(value)
    except:
        return 0.0

def round2(value):
    return round(value, 2)
