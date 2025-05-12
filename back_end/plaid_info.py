from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from cryptography.fernet import Fernet
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from database import SessionLocal
from models import Users
from auth import get_current_user
from dotenv import load_dotenv
from models import Users, Plaid_Bank_Account, Plaid_Transactions
from datetime import datetime, timedelta
from datetime import date

router = APIRouter(
    prefix='/plaid_info',
    tags=['plaid_info']
)

@router.get("/", status_code=status.HTTP_200_OK)
async def get_plaid_info(user: user_dependency, db: db_dependency):