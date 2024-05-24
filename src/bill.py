from typing import List
import subprocess
import jinja2
import os
from datetime import datetime
from decouple import config

from .apartment import Apartment
from .billing_line import BillingLine


class Bill:
    def __init__(self, meter_reading_date: str, due_date: str, apartment: Apartment, lines: List[BillingLine], total: str):
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.meter_reading_date = meter_reading_date
        self.due_date = due_date
        self.apartment = apartment
        self.lines = lines
        self.total = total
    
    def _get_invoice_number(self):
        yyyy_mm_dd = self.meter_reading_date.split("-")
        return f"{yyyy_mm_dd[0]}-{yyyy_mm_dd[1]}-{self.apartment.number}"
    
    def __repr__(self):
        return f"{self.meter_reading_date} - {self.apartment} - {self.total}€"
    
    def to_pdf(self):
        invoice_number = self._get_invoice_number()

        # get paths
        root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        templates_path = os.path.join(root_path, "templates")
        bills_path = os.path.join(root_path, "bills")
        bill_base_path = os.path.join(bills_path, invoice_number)
        bill_adoc_path = f"{bill_base_path}.adoc"
        bill_pdf_path = f"{bill_base_path}.pdf"

        # load the template
        template_loader = jinja2.FileSystemLoader(searchpath=templates_path)
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template("bill.adoc")

        # render the template
        output = template.render({
            "invoice_number": invoice_number,
            "apartment_number": self.apartment.number,
            "bill_date": self.date,
            "meter_reading_date": self.meter_reading_date,
            "due_date": self.due_date,
            "lines": self.lines,
            "customer_name": self.apartment.customer_name,
            "customer_email": self.apartment.customer_email,
            "customer_address": self.apartment.customer_address,
            "total": self.total
        })

        with open(bill_adoc_path, "w", encoding="utf8") as f:
            f.write(output)

        # run asciidoc to generate invoice.pdf
        cmd = config("ASCIIDOCTOR_BIN")
        subprocess.run(f"{cmd} {bill_adoc_path}", shell=True)

        return bill_pdf_path
