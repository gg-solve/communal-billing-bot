from typing import Dict


class Consumption:
    def __init__(self, values: Dict[str, str]):
        self.cold_water = float(values["külm"])
        self.hot_water = float(values["soe"])
        self.water = self.cold_water + self.hot_water
        self.gas = float(values["gaas"])
        self.electricity = float(values["elekter"])

    def __repr__(self) -> str:
        return f"Consumption(water={self.water} m3, gas={self.gas} m3, electricity={self.electricity} kWh)"
    