import os
import re
from typing import Optional, List, Annotated, Dict
from datetime import datetime, timedelta
from http.client import HTTPException
from fastapi import FastAPI, Query, File, UploadFile, HTTPException, Cookie, Depends, Response, Form, status, Request, Header
from pydantic import BaseModel, EmailStr, Field, validator
from models import load_config, settings
from logger import logger
import uuid
from itsdangerous import Signer
import logging
import hashlib
import hmac
import time
from packaging import version
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer
from passlib.context import CryptContext
import secrets
import bcrypt
from pydantic_settings import BaseSettings
from dataclasses import dataclass
from dotenv import load_dotenv
import jwt
from fastapi import Depends
from fastapi import FastAPI, Depends
import sqlite3
import asyncpg
from zoneinfo import ZoneInfo






