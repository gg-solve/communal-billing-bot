class BillingLine:
    def __init__(self, description: str, unit: str, amount: str, price: str):
        self.description = description.capitalize()
        self.unit = unit
        self.amount = amount
        self.price = price
    
    def __repr__(self):
        return f"{self.description}: {self.amount} {self.unit} - {self.price}€"
