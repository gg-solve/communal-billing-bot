class BillingItem:
    def __init__(self, description: str, unit: str):
        self.description = description
        self.unit = unit
    
    def __repr__(self):
        return f"{self.description} ({self.unit})"
