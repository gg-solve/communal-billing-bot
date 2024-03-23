#%%
from src.sheet_reader import SheetReader

reader = SheetReader()
bill = reader.get_bill("2024-03-01", "krt-3")
path = bill.to_pdf()
path

# bill.lines
# reader.get_consumption("2024-03-01", "krt-3")

# %%
