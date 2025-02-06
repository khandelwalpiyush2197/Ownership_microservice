from fastapi import HTTPException
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import subprocess
import yaml
import jwt
import datetime
import os
import secrets
import json
from dotenv import load_dotenv
from .vault_service import store_auth_token

# Load environment variables from .env file
load_dotenv()

# Load environment variables
NAMESPACE = os.getenv("NAMESPACE", "default")
OWNERSHIP_CONFIGMAP_NAME = os.getenv("OWNERSHIP_CONFIGMAP_NAME", "ownership-configmap")
INVENTORY_CONFIGMAP_NAME = os.getenv("INVENTORY_CONFIGMAP_NAME", "inventory-configmap")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))  # Replace with your actual secret key
INVENTORY_DATA = json.loads(os.getenv("INVENTORY_DATA", "{}"))
KUBERNETES_SERVICE_HOST = os.getenv("KUBERNETES_SERVICE_HOST")
KUBERNETES_TOKEN = os.getenv("KUBERNETES_TOKEN")
VAULT_URL = os.getenv("VAULT_URL")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")
ALGORITHM = "HS256"

# Load kubeconfig (from local or pod context)
try:
    config.load_kube_config()  # This will load from your local kubeconfig, if running outside a cluster.
except Exception as e:
    config.load_incluster_config()  # This is for when the code is running inside a Kubernetes pod.

def create_initial_config_map():
    """
    Creates the initial ConfigMap if it doesn't exist.
    """
    try:
        # Get the existing ConfigMap
        api_instance = client.CoreV1Api()
        try:
            config_map = api_instance.read_namespaced_config_map(name=OWNERSHIP_CONFIGMAP_NAME, namespace=NAMESPACE)
            print(f"ConfigMap '{OWNERSHIP_CONFIGMAP_NAME}' already exists.")
        except ApiException as e:
            if e.status == 404:
                # ConfigMap does not exist, create a new one
                config_map = client.V1ConfigMap(
                    metadata=client.V1ObjectMeta(name=OWNERSHIP_CONFIGMAP_NAME),
                    data={}
                )
                api_instance.create_namespaced_config_map(namespace=NAMESPACE, body=config_map)
                print(f"ConfigMap '{OWNERSHIP_CONFIGMAP_NAME}' created successfully.")
            else:
                raise HTTPException(status_code=500, detail=f"Kubernetes API error: {e}")
    except ApiException as e:
        if e.status == 404:
            # ConfigMap does not exist, create a new one
            config_map = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(name=OWNERSHIP_CONFIGMAP_NAME),
                data={}
            )
            api_instance.create_namespaced_config_map(namespace=NAMESPACE, body=config_map)
            print(f"ConfigMap '{OWNERSHIP_CONFIGMAP_NAME}' created successfully.")
        else:
            print(f"Exception when creating initial ConfigMap: {e}")
            raise HTTPException(status_code=500, detail=f"Kubernetes API error: {e}")
    except Exception as e:
        print(f"Exception when creating initial ConfigMap: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating initial ConfigMap: {e}")

def create_initial_inventory_config_map():
    """
    Creates the initial inventory ConfigMap if it doesn't exist.
    """
    try:
        # Get the existing ConfigMap
        api_instance = client.CoreV1Api()
        try:
            config_map = api_instance.read_namespaced_config_map(name=INVENTORY_CONFIGMAP_NAME, namespace=NAMESPACE)
            print(f"ConfigMap '{INVENTORY_CONFIGMAP_NAME}' already exists.")
        except ApiException as e:
            if e.status == 404:
                # ConfigMap does not exist, create a new one
                config_map = client.V1ConfigMap(
                    metadata=client.V1ObjectMeta(name=INVENTORY_CONFIGMAP_NAME),
                    data=INVENTORY_DATA
                )
                api_instance.create_namespaced_config_map(namespace=NAMESPACE, body=config_map)
                print(f"ConfigMap '{INVENTORY_CONFIGMAP_NAME}' created successfully.")
            else:
                raise HTTPException(status_code=500, detail=f"Kubernetes API error: {e}")
    except Exception as e:
        print(f"Exception when creating initial inventory ConfigMap: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating initial inventory ConfigMap: {e}")


def create_role_binding_and_generate_tokens(eid_list: list, role_name: str, num_days: int, pg_id: str, namespace_value: str) -> dict:
    """
    Creates Kubernetes RoleBindings for the given entity IDs, updates the YAML file, and generates auth tokens.

    Args:
        eid_list (list): The list of entity IDs for which the RoleBindings are created.
        role_name (str): The name of the existing Role to bind the users to.
        num_days (int): The number of days the RoleBindings are valid.
        pg_id (str): The playground ID.
        namespace_value (str): The namespace in which the RoleBindings are created.

    Returns:
        dict: A dictionary containing the auth tokens for the users associated with the eids.

    Raises:
        HTTPException: If there is an error calling the Kubernetes API.
    """
    try:
        tokens = {}

        for eid in eid_list:
            # Ensure eid is treated as a string
            eid_str = str(eid)

            # Define the RoleBinding YAML structure
            role_binding_yaml = {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "RoleBinding",
                "metadata": {
                    "name": f"map-{eid_str}",
                    "namespace": namespace_value  # Use the provided namespace
                },
                "roleRef": {
                    "apiGroup": "rbac.authorization.k8s.io",
                    "kind": "Role",
                    "name": role_name  # The role assigned to the user
                },
                "subjects": [
                    {
                        "kind": "User",
                        "apiGroup": "rbac.authorization.k8s.io",
                        "name": eid_str  # Provide the eid that needs playground access here
                    }
                ]
            }

            # Ensure the /temp_files directory exists
            os.makedirs("/temp_files", exist_ok=True)

            # Write the RoleBinding YAML to a temporary file
            role_binding_file_path = f"/app/temp_files/role_binding_{eid_str}.yaml"
            with open(role_binding_file_path, "w") as f:
                yaml.dump(role_binding_yaml, f)

            # Execute the kubectl command to apply the RoleBinding
            kubectl_command = [
                "kubectl", "apply", "-f", role_binding_file_path
            ]
            result = subprocess.run(kubectl_command, capture_output=True, text=True)

            if result.returncode != 0:
                raise HTTPException(status_code=500, detail=f"Failed to apply RoleBinding for {eid_str}: {result.stderr}")

            print(f"RoleBinding for user '{eid_str}' with role '{role_name}' applied successfully for {num_days} days.")

            # Generate auth token for the user associated with the eid
            token = generate_user_token(eid_str, num_days)
            tokens[eid_str] = token

            # Store the auth token in Vault
            # store_auth_token(eid_str, token)

            # Clean up the temporary file
            os.remove(role_binding_file_path)

        # Update ConfigMap to store num_days, eid, and pg_id
        update_config_map(pg_id, eid_list, num_days)

        return tokens

    except ApiException as e:
        print(f"Exception when calling Kubernetes API: {e}")
        raise HTTPException(status_code=500, detail=f"Kubernetes API error: {e}")
    except Exception as e:
        print(f"Exception when executing kubectl command: {e}")
        raise HTTPException(status_code=500, detail=f"Error executing kubectl command: {e}")



def generate_user_token(eid: str, num_days: int) -> str:
    """
    Generates an auth token for the user associated with the given entity ID.

    Args:
        eid (str): The entity ID for which the auth token is generated.
        num_days (int): The number of days the token is valid.

    Returns:
        str: The auth token for the user.

    Raises:
        HTTPException: If there is an error generating the token.
    """
    try:
        expiration = datetime.datetime.utcnow() + datetime.timedelta(days=num_days)
        payload = {
            "sub": eid,
            "exp": expiration
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating token: {e}")

def update_config_map(pg_id: str, eid_list: list, num_days: int):
    """
    Updates a Kubernetes ConfigMap to store the expiration date, eid, and pg_id.

    Args:
        pg_id (str): The playground ID.
        eid_list (list): The list of entity IDs.
        num_days (int): The number of days the RoleBindings are valid.

    Raises:
        HTTPException: If there is an error calling the Kubernetes API.
    """
    try:
        # Define the ConfigMap name
        config_map_name = OWNERSHIP_CONFIGMAP_NAME

        # Get the existing ConfigMap
        api_instance = client.CoreV1Api()
        try:
            config_map = api_instance.read_namespaced_config_map(name=config_map_name, namespace=NAMESPACE)
        except ApiException as e:
            if e.status == 404:
                # ConfigMap does not exist, create a new one
                config_map = client.V1ConfigMap(
                    metadata=client.V1ObjectMeta(name=config_map_name),
                    data={}
                )
                api_instance.create_namespaced_config_map(namespace=NAMESPACE, body=config_map)
            else:
                raise HTTPException(status_code=500, detail=f"Kubernetes API error: {e}")

        # Ensure the data attribute is initialized
        if config_map.data is None:
            config_map.data = {}

        # Update the ConfigMap data
        for eid in eid_list:
            key = f"{pg_id}-{eid}"
            expiration_date = (datetime.datetime.utcnow() + datetime.timedelta(days=num_days)).isoformat()
            config_map.data[key] = expiration_date

        # Apply the updated ConfigMap
        api_instance.patch_namespaced_config_map(name=config_map_name, namespace=NAMESPACE, body=config_map)

        print(f"ConfigMap '{config_map_name}' updated successfully.")
    except Exception as e:
        print(f"Exception when executing kubectl command: {e}")
        raise HTTPException(status_code=500, detail=f"Error executing kubectl command: {e}")

def update_inventory_status(pg_id: str, status: str):
    """
    Updates the inventory ConfigMap to set the status of a playground.

    Args:
        pg_id (str): The playground ID.
        status (str): The new status of the playground (e.g., "available", "unavailable").

    Raises:
        HTTPException: If there is an error calling the Kubernetes API.
    """
    try:
        # Get the existing ConfigMap
        api_instance = client.CoreV1Api()
        config_map = api_instance.read_namespaced_config_map(name=INVENTORY_CONFIGMAP_NAME, namespace=NAMESPACE)

        # Update the status of the specified playground
        if pg_id in config_map.data:
            size, _, namespace, group_name, environment, wb_bech_type = config_map.data[pg_id].split(',')
            config_map.data[pg_id] = f"{size},{status},{namespace},{group_name},{environment},{wb_bech_type}"

            # Apply the updated ConfigMap
            api_instance.patch_namespaced_config_map(name=INVENTORY_CONFIGMAP_NAME, namespace=NAMESPACE, body=config_map)
            print(f"ConfigMap '{INVENTORY_CONFIGMAP_NAME}' updated successfully with pg_id '{pg_id}' set to '{status}'.")
        else:
            raise HTTPException(status_code=404, detail=f"Playground ID '{pg_id}' not found in inventory")
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Kubernetes API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating inventory status: {e}")