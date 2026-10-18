from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="LNX Vision API",
    description="API pour gérer les chemins dans LNX Vision",
    version="1.0.0"
)

# Autorise les appels depuis n'importe quelle origine (fichier HTML local inclus)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")