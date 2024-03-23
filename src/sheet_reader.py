from typing import List
import gspread
from gspread import Worksheet
import numpy as np
from decouple import config
import re

from .apartment import Apartment
from .bill import Bill
from .billing_item import BillingItem
from .billing_line import BillingLine
from .consumption import Consumption
from .utils import get_apartment_number_from_name, normalize_date


class SheetReader:
    def __init__(self):
        self._gc = gspread.service_account(filename=config("SERVICE_ACCOUNT_PATH"))
        self._sheet = self._gc.open_by_key(config("SHEET_KEY"))
        self._bills_values = np.array(self._get_bills_sheet().get_all_values())
        self._apartments_values = np.array(self._get_apartments_sheet().get_all_values())
        self._billing_lines_values = np.array(self._get_units_sheet().get_all_values())
        self._consumption_values = np.array(self._get_consumption_sheet().get_all_values())

        # parse dates and apartments immediately
        self._dates = self._parse_dates()
        self._apartments = self._parse_apartments()
        self._billing_items = self._parse_billing_items()
    
    def _get_bills_sheet(self) -> Worksheet:
        return self._sheet.worksheet(config("BILLS_SHEET_NAME"))

    def _get_apartments_sheet(self) -> Worksheet:
        return self._sheet.worksheet(config("APARTMENTS_SHEET_NAME"))
    
    def _get_units_sheet(self) -> Worksheet:
        return self._sheet.worksheet(config("BILLING_LINES_SHEET_NAME"))
    
    def _get_consumption_sheet(self) -> Worksheet:
        return self._sheet.worksheet(config("CONSUMPTION_SHEET_NAME"))

    # get dates in yyyy-mm-dd format
    def _parse_dates(self) -> List[str]:
        values = self._bills_values
        dates = []

        for value in values[2:,0]:
            try:
                dates.append(normalize_date(value))
            except ValueError:
                continue
        
        return dates
    
    def _parse_apartments(self) -> List[Apartment]:
        headers = self._apartments_values[0]
        apartments = []
        
        for row in self._apartments_values[1:]:
            try:
                apartment = dict(zip(headers, row))
                apartments.append(Apartment(
                    apartment["korter"],
                    apartment["ruutmeetrid"],
                    str(round(float(apartment["mõtteline osa"]) * 100, 2)) + "%",
                    apartment["arve saaja"],
                    apartment["arve saaja email"],
                    apartment["arve saaja aadress"]))
            except ValueError:
                pass

        return apartments
    
    def _parse_billing_items(self) -> List[BillingItem]:
        values = self._billing_lines_values
        headers = values[0]
        billing_items = []

        for row in values[1:]:
            billing_item = dict(zip(headers, row))
            billing_items.append(BillingItem(billing_item["kirjeldus"], billing_item["ühik"]))
        
        return billing_items
    
    def get_apartments(self) -> List[Apartment]:
        return self._apartments
    
    def get_dates(self) -> List[str]:
        return self._dates
    
    def get_billing_items(self) -> List[BillingItem]:
        return self._billing_items
    
    def _get_billing_date_row_index(self, date: str):
        date_index = self._dates.index(date)

        if date_index == -1:
            raise ValueError(f"Date {date} not found in billing sheet")

        return self._dates.index(date) + 2

    # get consumption for apartment and date
    def get_consumption(self, date: str, apartment_slug: str):
        # Get date row index and apartment number
        row_index = self._get_billing_date_row_index(date)
        apartment_number = get_apartment_number_from_name(apartment_slug)

        # Get apartment column index in consumption sheet
        column_index = None

        for i, value in enumerate(self._consumption_values[0]):
            try:
                value_apartment_number = get_apartment_number_from_name(value)
            except ValueError:
                continue

            if value_apartment_number == apartment_number:
                column_index = i
                break
        
        if column_index is None:
            raise ValueError(f"Apartment {apartment_slug} not found in consumption sheet")
        
        # Get consumption values
        header = self._consumption_values[1,column_index:column_index+5]
        values = self._consumption_values[row_index,column_index:column_index+5]

        return Consumption(dict(zip(header, values)))


    # get billing values for apartment and date
    def get_billing_values(self, date: str, apartment_slug: str):
        # Get date row index and apartment number
        row_index = self._get_billing_date_row_index(date)
        apartment_number = get_apartment_number_from_name(apartment_slug)

        # Get apartment column index in bills sheet
        column_index = None

        for i, value in enumerate(self._bills_values[0]):
            try:
                value_apartment_number = get_apartment_number_from_name(value)
            except ValueError:
                continue

            if value_apartment_number == apartment_number:
                column_index = i
                break
        
        if column_index is None:
            raise ValueError(f"Apartment {apartment_slug} not found in billing sheet")

        # Get billing item values
        billing_items = self.get_billing_items()
        header = self._bills_values[1,column_index:column_index+len(billing_items)+1]
        values = self._bills_values[row_index,column_index:column_index+len(billing_items)+1]
        
        return dict(zip(header, values))

    def get_apartment(self, apartment_slug: str):
        for apartment in self._apartments:
            if apartment.slug == apartment_slug:
                return apartment
        
        raise ValueError(f"Apartment {apartment_slug} not found in apartments sheet")
    
    def _get_total_hot_water_consumption(self, row_index: int):
        column = int(config("TOTAL_HOT_WATER_CONSUMPTION_COLUMN"))
        return float(self._consumption_values[row_index, column])

    def _get_communal_gas_consumption(self, row_index: int):
        column = int(config("COMMUNAL_GAS_CONSUMPTION_COLUMN"))
        return float(self._consumption_values[row_index, column])

    def _get_due_date(self, row_index: int):
        column = int(config("DUE_DATE_COLUMN"))
        return normalize_date(self._bills_values[row_index, column])

    # get bill for apartment and date
    def get_bill(self, date: str, apartment_slug: str):
        # Get apartment
        apartment = self.get_apartment(apartment_slug)

        # Get date row index
        date_row_index = self._get_billing_date_row_index(date)
        
        # Get consumption
        consumption = self.get_consumption(date, apartment_slug)

        # Get due date
        due_date = self._get_due_date(date_row_index)

        # Generate billing lines
        billing_values = self.get_billing_values(date, apartment_slug)
        billing_lines = []
        billing_items = self.get_billing_items()

        for item in billing_items:
            if not item.description in billing_values:
                raise ValueError(f"Item {item.description} not found in billing sheet")

            if item.unit == "m2":
                amount = apartment.size
            elif item.unit == "m2 %" or item.unit == "m2%" or item.unit == "maja":
                amount = apartment.size_ratio
            elif item.description == "elekter":
                amount = str(round(consumption.electricity, 2))
            elif item.description == "vesi":
                amount = str(round(consumption.water, 2))
            elif item.description == "gaas - küte":
                amount = str(round(consumption.gas, 2))
            elif item.description == "gaas - vesi":
                total_hot_water_consumption = self._get_total_hot_water_consumption(date_row_index)
                communal_gas_consumption = self._get_communal_gas_consumption(date_row_index)
                amount = str(round(consumption.hot_water / total_hot_water_consumption * communal_gas_consumption, 2))
            else:
                amount = "N/A"
            
            billing_lines.append(BillingLine(item.description, item.unit, amount, billing_values[item.description]))

        return Bill(date, due_date, apartment, billing_lines, billing_values["kokku"])
