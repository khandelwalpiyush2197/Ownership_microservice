import subprocess
import os
import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List
from .schemas import TriggerSparkPipelineRequest, TriggerSparkPipelineResponse
from .utils import validate_token
from app.modules.ownership.utils.logger import logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load environment variables
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploaded_files")
KUBERNETES_SERVICE_HOST = os.getenv("KUBERNETES_SERVICE_HOST")
KUBERNETES_TOKEN = os.getenv("KUBERNETES_TOKEN")
NAMESPACE = os.getenv("NAMESPACE", "default")

router = APIRouter()

@router.post("/trigger_spark_pipeline", response_model=TriggerSparkPipelineResponse)
async def trigger_spark_pipeline(
    pg_id: str = Form(...),
    auth_token: str = Form(...),
    sparkyaml: UploadFile = File(...),
    pyfiles: List[UploadFile] = File(...)
):
    """
    Triggers a Tekton pipeline to run a Spark job.

    Args:
        pg_id (str): The playground ID.
        auth_token (str): The authorization token.
        sparkyaml (UploadFile): The Spark YAML file.
        pyfiles (List[UploadFile]): The list of Python files.

    Returns:
        dict: A dictionary containing the status of the pipeline trigger.
    """
    try:
        # Validate the authorization token
        # if not validate_token(pg_id, auth_token):
        #     raise HTTPException(status_code=401, detail="Invalid authorization token")

        # Ensure the uploaded_files directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Save the uploaded Spark YAML file to disk
        sparkyaml_path = os.path.join(UPLOAD_DIR, sparkyaml.filename)
        with open(sparkyaml_path, "wb") as f:
            f.write(await sparkyaml.read())

        # Save the uploaded Python files to disk
        pyfile_paths = []
        for pyfile in pyfiles:
            pyfile_path = os.path.join(UPLOAD_DIR, pyfile.filename)
            pyfile_paths.append(pyfile_path)
            with open(pyfile_path, "wb") as f:
                f.write(await pyfile.read())

        # Create a PipelineRun JSON object
        pipeline_run_json = {
            "apiVersion": "tekton.dev/v1beta1",
            "kind": "PipelineRun",
            "metadata": {
                "generateName": "spark-pipeline-run-"
            },
            "spec": {
                "pipelineRef": {
                    "name": "bitbucket-pr-pipeline"
                },
                "workspaces": [
                    {
                        "name": "shared-workspace",
                        "persistentVolumeClaim": {
                            "claimName": "pvc-spark"
                        }
                    }
                ],
                "params": [
                    {
                        "name": "sparkyaml",
                        "value": sparkyaml_path
                    }
                ]
            }
        }

        for i, pyfile_path in enumerate(pyfile_paths):
            pipeline_run_json["spec"]["params"].append({
                "name": f"pyfile{i+1}",
                "value": pyfile_path
            })

        # Convert the PipelineRun JSON object to a string
        pipeline_run_json_str = json.dumps(pipeline_run_json)

        # Execute the kubectl command to create the PipelineRun
        kubectl_command = [
            "kubectl", "create", "-f", "-"
        ]
        result = subprocess.run(kubectl_command, input=pipeline_run_json_str, capture_output=True, text=True)

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to trigger Tekton pipeline: {result.stderr}")

        # Delete the uploaded files after successful pipeline trigger
        os.remove(sparkyaml_path)
        for pyfile_path in pyfile_paths:
            os.remove(pyfile_path)

        return {"status": "Pipeline triggered successfully", "output": result.stdout}
    except Exception as e:
        logger.error(f"Error triggering Tekton pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Error triggering Tekton pipeline: {str(e)}")