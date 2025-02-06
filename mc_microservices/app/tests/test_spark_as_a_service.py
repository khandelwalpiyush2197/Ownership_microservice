from fastapi.testclient import TestClient
from mc_microservices.main import app

client = TestClient(app)

def test_trigger_spark_pipeline():
    sparkyaml_content = """
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: spark-config
    data:
      config.yaml: |
        spark:
          master: "local[*]"
          appName: "TestApp"
    """
    pyfile_content = """
    print("Hello, Spark!")
    """

    files = {
        "sparkyaml": ("sparkyaml.yaml", sparkyaml_content, "text/yaml"),
        "pyfile": ("script.py", pyfile_content, "text/x-python")
    }

    response = client.post("/spark/trigger_spark_pipeline", files=files)
    assert response.status_code == 200
    assert "Pipeline triggered successfully" in response.json()["status"]

def test_spark_job_status():
    job_id = "test-job-id"
    response = client.get(f"/spark/spark_job_status", params={"job_id": job_id})
    assert response.status_code == 200
    assert "status" in response.json()