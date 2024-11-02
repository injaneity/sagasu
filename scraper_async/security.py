import base64
import os
from dotenv import load_dotenv
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

load_dotenv()

def load_private_key():
    private_key_b64 = os.getenv("PRIVATE_KEY")
    if not private_key_b64:
        raise ValueError("PRIVATE_KEY not found in environment variables.")
    
    private_key_data = base64.b64decode(private_key_b64)
    private_key = serialization.load_pem_private_key(private_key_data, password=None)
    return private_key

def load_public_key():
    public_key_b64 = os.getenv("PUBLIC_KEY")
    if not public_key_b64:
        raise ValueError("PUBLIC_KEY not found in environment variables.")
    
    public_key_data = base64.b64decode(public_key_b64)
    public_key = serialization.load_pem_public_key(public_key_data)
    return public_key

def encrypt_data_rsa(data):
    public_key = load_public_key()
    encrypted = public_key.encrypt(
        data.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted

def decrypt_data_rsa(encrypted_data):
    private_key = load_private_key()  # Load the private key
    decrypted = private_key.decrypt(
        encrypted_data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted.decode()
