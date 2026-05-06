from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
load_dotenv()

import os
import json

def get_credentials():
    import streamlit as st
    
    # Try Streamlit secrets first, fall back to env var
    try:
        creds_dict = st.secrets["GCP_SERVICE_ACCOUNT"]
    except Exception:
        creds_json = os.getenv("GCP_SERVICE_ACCOUNT")
        if not creds_json:
            raise ValueError("Missing GCP_SERVICE_ACCOUNT — add to secrets.toml or env")
        creds_dict = json.loads(creds_json)

    return Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )


def get_sheets_service():
    creds = get_credentials()
    return build('sheets', 'v4', credentials=creds)
