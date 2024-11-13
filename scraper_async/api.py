from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from scraper import scrape_smu_fbs
from pydantic import BaseModel
import yaml
from security import encrypt_data_rsa, decrypt_data_rsa, load_public_key, load_private_key
from cryptography.hazmat.primitives import serialization
from exceptions import FrameNotFoundException

app = FastAPI()

def load_constants(config_path='constants.yaml'):
    try:
        with open(config_path, 'r') as file:
            constants = yaml.safe_load(file)
        return constants
    except FileNotFoundError:
        print(f"Configuration file {config_path} not found.")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        exit(1)

constants = load_constants()

class Credentials(BaseModel):
    username: str
    password: str

class ScrapeRequest(BaseModel):
    credentials: Credentials
    date_raw: str
    duration_hours: float
    start_time: str
    building_names: Optional[List[str]] = []
    floors: Optional[List[str]] = []
    facility_types: Optional[List[str]] = []
    equipment: Optional[List[str]] = []

private_key = load_private_key()
public_key = load_public_key()

@app.get("/public-key", response_class=PlainTextResponse)
def get_public_key():
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('utf-8')

''' 
THIS IS ONLY FOR TESTING: DO NOT USE THIS IN PRODUCTION
'''
@app.post("/encrypt_credentials")
def encrypt_credentials(credentials: Credentials):
    try:
        encrypted_username = encrypt_data_rsa(credentials.username)
        encrypted_password = encrypt_data_rsa(credentials.password)
        
        return {
            "encrypted_username": encrypted_username.hex(),
            "encrypted_password": encrypted_password.hex()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape")
async def scrape_endpoint(request: ScrapeRequest):
    try:
        
        try:
            encrypted_username_bytes = bytes.fromhex(request.credentials.username)
            encrypted_password_bytes = bytes.fromhex(request.credentials.password)
            decrypted_username = decrypt_data_rsa(encrypted_username_bytes)
            decrypted_password = decrypt_data_rsa(encrypted_password_bytes)
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}. Ensure credentials are encrypted and in hexadecimal format.")
        except FrameNotFoundException as fnf_error:
            raise HTTPException(status_code=404, detail=str(fnf_error))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Unexpected error during decryption: {str(e)}.")
        
        # Update the request with decrypted credentials
        request.credentials.username = decrypted_username
        request.credentials.password = decrypted_password

        # Pass the request data to the scraping function
        data = await scrape_smu_fbs(request, constants)
        if data:
            return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
