import secrets
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
import re
from decouple import config

from .sheet_reader import SheetReader

app = FastAPI()
security = HTTPBasic()
templates = Jinja2Templates(directory="templates")

def check_credentials(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = config("ADMIN_USERNAME").encode("utf8")
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = config("ADMIN_PASSWORD").encode("utf8")
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    check_credentials(credentials)

    reader = SheetReader()
    apartments = reader.get_apartments()
    dates = reader.get_dates()

    return templates.TemplateResponse(request=request, name="index.html", context={
        "apartments": apartments,
        "dates": dates
    })


@app.get("/{filename}.pdf")
def get_bill(filename: str, credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    check_credentials(credentials)
    
    match = re.match(r"arve-(\d{4}-\d{2}-\d{2})-(.*)", filename)

    if not match:
        raise ValueError(f"Invalid filename {filename}")
    
    date = match.group(1)
    apartment_slug = match.group(2)
    reader = SheetReader()
    bill = reader.get_bill(date, apartment_slug)
    
    return FileResponse(bill.to_pdf(), media_type="application/pdf")
