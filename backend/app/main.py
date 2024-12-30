from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import init_router

from . import config
from . import models

def create_app():
    settings = config.get_settings()
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    init_router(app)

    models.init_db(settings)


    @app.on_event("startup")
    async def on_startup():
        await models.recreate_table()

    return app