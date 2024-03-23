from .utils import get_apartment_number_from_name


class Apartment:
    def __init__(self, name: str, size: str, size_ratio: str, customer_name: str, customer_email: str, customer_address: str):
        self.name = name
        self.size = size
        self.size_ratio = size_ratio
        self.number = get_apartment_number_from_name(name)

        if self.number is None:
            raise ValueError(f"Apartment number not found in name {name}")
        
        self.slug = name.replace(" ", "-")
        self.customer_name = customer_name
        self.customer_email = customer_email
        self.customer_address = customer_address
    
    def __repr__(self):
        return f"{self.name} ({self.customer_name})"
