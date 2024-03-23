import re


def get_apartment_number_from_name(name: str) -> int:
    apartment_number_match = re.match(r".*(\d+).*", name)
    
    if not apartment_number_match:
        raise ValueError(f"Apartment number not found in name {name}")
    
    return int(apartment_number_match.group(1))

def normalize_date(value: str) -> str:
    d_m_yyyy_match = re.match(r"(\d{1,2}).(\d{1,2}).(\d{4})", value)
    yyyy_m_d_match = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", value)
    
    if d_m_yyyy_match:
        d, m, yyyy = d_m_yyyy_match.groups()
        return f"{yyyy}-{m.zfill(2)}-{d.zfill(2)}"
    
    if yyyy_m_d_match:
        yyyy, m, d = yyyy_m_d_match.groups()
        return f"{yyyy}-{m.zfill(2)}-{d.zfill(2)}"

    raise ValueError(f"Date {value} does not match any known format")
