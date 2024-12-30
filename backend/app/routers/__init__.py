from . import user
from . import authentication
def init_router(app):
    app.include_router(user.router)
    app.include_router(authentication.router)