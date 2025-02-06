# MC Microservices Project

## Overview
The MC Microservices Project is designed to provide a scalable and efficient architecture for managing microservices. This project aims to demonstrate the implementation of microservices using modern technologies and best practices.

## Features
- **Scalability**: Easily scale services based on demand.
- **Resilience**: Robust error handling and recovery mechanisms.
- **Flexibility**: Modular design allowing easy addition and modification of services.
- **Efficiency**: Optimized for performance and resource utilization.

## Getting Started
To get started with the MC Microservices Project, follow these steps:

1. **Clone the repository**:
    ```sh
    git clone https://github.com/yourusername/mc_microservices.git
    ```
2. **Navigate to the project directory**:
    ```sh
    cd mc_microservices
    ```
3. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```
4. **Start the services**:
    ```sh
    uvicorn app.main:app --reload
    ```

## Project Structure
mc_microservices/
    .gitignore
    app/
        __pycache__/
        app_instance.py
        main.py
        modules/
            __init__.py
            __pycache__/
            healthcheck/
                __pycache__/
                api.py
            ownership/
                __init__.py
                __pycache__/
                api.py
                config/
                models/
                    __init__.py
                    ownership_record.py
                schemas/
                    __init__.py
                    claim_ownership_request.py
                services/
                    __init__.py
                    kubernetes_service.py
                utils/
            relinquish/
            spark_as_a_service/
            store/
            utils/
            validate/
        tests/
            test_healthcheck.py
            test_ownership.py
            test_relinquish.py
            test_spark_as_a_service.py
            test_validate.py
    Dockerfile
    README.md
    requirements.txt


### Key Components

- **`app/main.py`**:
    - Entry point of the FastAPI application.
    - Initializes the FastAPI app and includes the router from the `ownership` module.

- **`app/modules/ownership/api.py`**:
    - Defines the API endpoints for the ownership module.
    - Includes endpoints to claim, relinquish, and validate ownership of resources.

- **`app/modules/ownership/models/__init__.py`**:
    - Defines the data models for the ownership module.
    - Manages resource ownership and performs operations like claiming, relinquishing, and validating ownership.

- **`app/modules/ownership/schemas/ownership.py`**:
    - Defines Pydantic models for request and response validation.

- **`app/modules/ownership/services/ownership_service.py`**:
    - Contains business logic and service functions for the ownership module.

- **`app/modules/ownership/utils/logger.py`**:
    - Utility module for logging.

- **`Dockerfile`**:
    - Defines the Docker image for the project.
    - Uses a Python 3.8 slim image, sets the working directory, copies the project files, installs dependencies, exposes port 80, and defines the command to run the application.

- **`requirements.txt`**:
    - Lists the dependencies required for the project.

- **`.gitignore`**:
    - Specifies the files and directories to be ignored by Git.

## Running with Docker

1. **Build the Docker image**:
    ```sh
    docker build -t mc_microservices .
    ```

2. **Run the Docker container**:
    ```sh
    docker run -p 80:80 mc_microservices
    ```

## Running Tests

To run the unit tests, use `pytest`. Make sure `pytest` is installed:

```sh
pip install pytest
```

Then run the tests:
pytest tests/

```sh

## License
This project is licensed under ******






