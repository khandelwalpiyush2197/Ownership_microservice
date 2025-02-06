from fastapi import APIRouter, HTTPException
from .schemas.claim_ownership_request import ClaimOwnershipRequest
from .services.kubernetes_service import create_role_binding_and_generate_tokens, update_inventory_status
from kubernetes import client
from kubernetes.client.rest import ApiException
import os
from dotenv import load_dotenv
from typing import Tuple

# Load environment variables from .env file
load_dotenv()

# Load environment variables
ROLE_NAME = os.getenv("ROLE_NAME", "cluster-full-access-role")

router = APIRouter()

def check_kubernetes_resources(eid_list: list):
    """
    Checks if the service account for each eid in the eid_list exists in any namespace in the cluster,
    and if the given role name (ClusterRole or Role) is available in the cluster.

    Args:
        eid_list (list): The list of entity IDs (users).

    Raises:
        HTTPException: If the service account or role name does not exist.
    """
    try:
        api_instance = client.CoreV1Api()
        rbac_api_instance = client.RbacAuthorizationV1Api()

        # Check if the ClusterRole exists
        role_found = False
        try:
            rbac_api_instance.read_cluster_role(name=ROLE_NAME)
            role_found = True
        except ApiException as e:
            if e.status != 404:
                raise HTTPException(status_code=500, detail=f"Kubernetes API error: {e}")

        # If ClusterRole is not found, check if the Role exists in any namespace
        namespaces = api_instance.list_namespace().items
        if not role_found:
            for ns in namespaces:
                try:
                    rbac_api_instance.read_namespaced_role(name=ROLE_NAME, namespace=ns.metadata.name)
                    role_found = True
                    break
                except ApiException as e:
                    if e.status != 404:
                        raise HTTPException(status_code=500, detail=f"Kubernetes API error: {e}")
            if not role_found:
                raise HTTPException(status_code=404, detail=f"Role '{ROLE_NAME}' not found as ClusterRole or in any namespace")

        # Check if the users exist in any namespace
        for eid in eid_list:
            user_found = False
            for ns in namespaces:
                try:
                    api_instance.read_namespaced_service_account(name=eid, namespace=ns.metadata.name)
                    user_found = True
                    break
                except ApiException as e:
                    if e.status != 404:
                        raise HTTPException(status_code=500, detail=f"Kubernetes API error: {e}")
            if not user_found:
                raise HTTPException(status_code=404, detail=f"User '{eid}' not found in any namespace")

    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Kubernetes API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking Kubernetes resources: {e}")

def check_inventory(size: str, environment: str) -> Tuple[str, str]:
    """
    Checks the inventory for an available playground of the specified size and environment.

    Args:
        size (str): The size of the playground.
        environment (str): The environment of the playground.

    Returns:
        tuple: The playground ID and namespace if available, otherwise raises an HTTPException.
    """
    try:
        config_map_name = "inventory-configmap"
        namespace = 'default'  # Use 'default' namespace

        # Get the existing ConfigMap
        api_instance = client.CoreV1Api()
        config_map = api_instance.read_namespaced_config_map(name=config_map_name, namespace=namespace)

        # Check for available playgrounds of the specified size and environment
        for pg_id, value in config_map.data.items():
            size_value, availability, namespace_value, group_name, environment_value, wb_bech_type = value.split(',')
            if size_value == size and availability == "available":
                return pg_id, namespace_value

        raise HTTPException(status_code=404, detail="No available playgrounds of the specified size and environment")
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Kubernetes API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking inventory: {e}")

@router.post("/claim_ownership")
async def claim_ownership(request: ClaimOwnershipRequest):
    """
    Claims ownership of resources by creating necessary Kubernetes resources and returning a unique playground ID and auth tokens for each eid.

    Args:
        request (ClaimOwnershipRequest): The request payload containing ownership details.

    Returns:
        dict: A dictionary containing the playground ID and a list of auth tokens for each eid.

    Raises:
        HTTPException: If there is an error during the ownership claim process.
    """
    try:
        # Extract parameters from request data
        eid_list = request.eid_list
        num_days = request.num_days
        size = request.size
        environment = request.environment
        wb_bech_type = request.wb_bech_type

        # Check if the service account for each eid and the role name (ClusterRole or Role) exist in the cluster
        check_kubernetes_resources(eid_list)

        # Get playground ID from inventory
        pg_id, namespace_value = check_inventory(size=size, environment=environment)

        if not pg_id:
            raise HTTPException(status_code=404, detail="No available playgrounds of the specified size and environment")

        # Create RoleBinding in Kubernetes and get tokens
        auth_tokens = create_role_binding_and_generate_tokens(eid_list, ROLE_NAME, num_days, pg_id, namespace_value)

        # Update ConfigMap status to "unavailable"
        update_inventory_status(pg_id, "unavailable")

        # Return ownership assignment confirmation with pg_id and auth tokens
        return {
            "pg_id": pg_id,
            "auth_tokens": auth_tokens
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Kubernetes API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))