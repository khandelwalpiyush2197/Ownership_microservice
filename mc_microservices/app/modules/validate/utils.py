import hvac
from fastapi import HTTPException
from app.modules.ownership.utils.logger import logger
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

VAULT_URL = os.getenv("VAULT_URL")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")

client = hvac.Client(
    url=VAULT_URL,
    token=VAULT_TOKEN,
)

def get_token_from_vault(eid: str):
    try:
        logger.debug(f"Fetching token for eid {eid} from Vault...")
        # Access Vault and get the stored token for the given eid
        secret_path = f"auth-tokens/{eid}"  # Adjust this path based on your Vault structure
        response = client.secrets.kv.read_secret_version(path=secret_path)
        stored_token = response['data']['data']['token']  # Adjust based on Vault secret structure
        logger.debug(f"Retrieved token for eid {eid}: {stored_token}")
        return stored_token
    except hvac.exceptions.InvalidPath as e:
        logger.error(f"Error fetching token from Vault for eid {eid}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")