from fastapi import APIRouter, HTTPException
from kubernetes import client
from kubernetes.client.rest import ApiException
from app.modules.ownership.services.kubernetes_service import update_inventory_status
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Load environment variables
NAMESPACE = os.getenv("NAMESPACE", "default")
OWNERSHIP_CONFIGMAP_NAME = os.getenv("OWNERSHIP_CONFIGMAP_NAME", "ownership-configmap")

router = APIRouter()

def check_all_eids_relinquished(pg_id: str) -> bool:
    """
    Checks if all eids associated with the given pg_id are relinquished.

    Args:
        pg_id (str): The playground ID.

    Returns:
        bool: True if all eids are relinquished, False otherwise.
    """
    try:
        # Get the existing ConfigMap
        api_instance = client.CoreV1Api()
        config_map = api_instance.read_namespaced_config_map(name=OWNERSHIP_CONFIGMAP_NAME, namespace=NAMESPACE)

        # Check if any eids are still associated with the pg_id
        for key in config_map.data.keys():
            if key.startswith(pg_id):
                return False

        return True
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Kubernetes API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking eids: {e}")

def relinquish_expired_eids():
    """
    Relinquishes ownership of resources for expired eids by deleting the associated Kubernetes RoleBinding and updating the inventory ConfigMap.
    """
    try:
        # Get the existing ConfigMap
        api_instance = client.CoreV1Api()
        config_map = api_instance.read_namespaced_config_map(name=OWNERSHIP_CONFIGMAP_NAME, namespace=NAMESPACE)

        # Check for expired eids and relinquish them
        for key, expiration_date in config_map.data.items():
            pg_id, eid = key.split('-')
            if expiration_date >= datetime.utcnow():
                # Delete the RoleBinding
                role_binding_name = f"map-{eid}"
                api_instance.delete_namespaced_role_binding(name=role_binding_name, namespace=NAMESPACE)

                # Update inventory ConfigMap status to "available" if all eids are relinquished
                if check_all_eids_relinquished(pg_id):
                    update_inventory_status(pg_id, "available")

                # Remove the eid from the ownership ConfigMap
                del config_map.data[key]

        # Apply the updated ConfigMap
        api_instance.patch_namespaced_config_map(name=OWNERSHIP_CONFIGMAP_NAME, namespace=NAMESPACE, body=config_map)

        print("Expired eids relinquished successfully.")
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Kubernetes API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error relinquishing expired eids: {e}")

# Schedule the relinquish_expired_eids function to run every day
scheduler = BackgroundScheduler()
scheduler.add_job(relinquish_expired_eids, 'interval', days=1)
scheduler.start()

@router.delete("/relinquish_ownership")
async def relinquish_ownership(pg_id: str, eid: str):
    """
    Relinquishes ownership of resources by deleting the associated Kubernetes RoleBinding and updating the inventory ConfigMap.

    Args:
        pg_id (str): The playground ID.
        eid (str): The entity ID.

    Returns:
        dict: A dictionary containing the status of the relinquishment.

    Raises:
        HTTPException: If there is an error during the relinquishment process.
    """
    try:
        role_binding_name = f"map-{eid}"

        # Delete the RoleBinding
        api_instance = client.RbacAuthorizationV1Api()
        api_instance.delete_namespaced_role_binding(name=role_binding_name, namespace=NAMESPACE)

        # Check if all eids associated with the pg_id are relinquished
        if check_all_eids_relinquished(pg_id):
            # Update inventory ConfigMap status to "available"
            update_inventory_status(pg_id, "available")

        return {"status": "Ownership relinquished successfully"}
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Kubernetes API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error relinquishing ownership: {e}")