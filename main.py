from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse
from app.modules.ownership.utils.logger import logger
from app.modules.ownership import api as ownership_api
from app.modules.healthcheck import api as healthcheck_api
from app.modules.relinquish import api as relinquish_api
from app.modules.validate import api as validate_api
from app.modules.spark_as_a_service import api as spark_api
from app.modules.ownership.services.kubernetes_service import create_initial_config_map, create_initial_inventory_config_map

# Initialize FastAPI app
app = FastAPI(
    title="MC Microservices",
    description="A scalable and efficient architecture for managing microservices",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP error occurred: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"Validation error occurred: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"message": "Validation error", "errors": exc.errors()},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"An error occurred: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )

@app.on_event("startup")
async def startup_event():
    try:
        create_initial_config_map()
        create_initial_inventory_config_map()
        logger.info("ConfigMaps initialized successfully.")
    except Exception as e:
        logger.error(f"Error during startup: {e}")

# Include routers from different modules
app.include_router(ownership_api.router, prefix="/ownership", tags=["ownership"])
app.include_router(healthcheck_api.router, prefix="/healthcheck", tags=["healthcheck"])
app.include_router(relinquish_api.router, prefix="/relinquish", tags=["relinquish"])
app.include_router(validate_api.router, prefix="/validate", tags=["validate"])
app.include_router(spark_api.router, prefix="/spark", tags=["spark"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Microservices Application"}