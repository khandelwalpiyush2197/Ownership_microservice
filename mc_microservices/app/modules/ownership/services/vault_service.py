import hvac
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

VAULT_URL = os.getenv("VAULT_URL")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")

client = hvac.Client(
    url=VAULT_URL,
    token=VAULT_TOKEN,
)

def store_auth_token(eid: str, token: str):
    """
    Stores the auth token in HashiCorp Vault.

    Args:
        eid (str): The entity ID for which the auth token is generated.
        token (str): The auth token to store.

    Raises:
        Exception: If there is an error storing the token in Vault.
    """
    try:
        secret_path = f"auth-tokens/{eid}"
        client.secrets.kv.v2.create_or_update_secret(
            path=secret_path,
            secret={"token": token},
        )
        print(f"Auth token for user '{eid}' stored in Vault successfully.")
    except Exception as e:
        print(f"Exception when storing auth token in Vault: {e}")
        raise Exception(f"Error storing auth token in Vault: {e}")

def delete_auth_token(eid: str):
    """
    Deletes the auth token from HashiCorp Vault.

    Args:
        eid (str): The entity ID for which the auth token is deleted.

    Raises:
        Exception: If there is an error deleting the token from Vault.
    """
    try:
        secret_path = f"auth-tokens/{eid}"
        client.secrets.kv.v2.delete_metadata_and_all_versions(path=secret_path)
        print(f"Auth token for user '{eid}' deleted from Vault successfully.")
    except Exception as e:
        print(f"Exception when deleting auth token from Vault: {e}")
        raise Exception(f"Error deleting auth token from Vault: {e}")