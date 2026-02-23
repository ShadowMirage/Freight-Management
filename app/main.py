from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import users, trucks, loads, bookings

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json")

# Include Routers
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(trucks.router, prefix=f"{settings.API_V1_STR}/trucks", tags=["trucks"])
app.include_router(loads.router, prefix=f"{settings.API_V1_STR}/loads", tags=["loads"])
app.include_router(bookings.router, prefix=f"{settings.API_V1_STR}/bookings", tags=["bookings"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
