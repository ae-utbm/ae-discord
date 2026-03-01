from aiohttp import web
from aiohttp.web import Application, AppRunner, Request, Response, TCPSite, post
from pydantic import BaseModel, ValidationError

from src.client import SithClient, UserSchema
from src.main import AeBot
from src.services.auth import AuthService, MemberNotFound


class CallbackData(BaseModel):
    user: UserSchema
    signature: str


async def login_callback(request: Request) -> Response:
    try:
        user_id = int(request.match_info["user_id"])
        d = await request.read()
        data = CallbackData.model_validate_json(d)
    except (ValueError, ValidationError):
        return web.HTTPUnprocessableEntity()
    service: AuthService = request.app["auth-service"]
    try:
        await service.sync_user(user_id, data.user)
    except MemberNotFound:
        return web.HTTPNotFound()
    return web.HTTPOk()


async def start_server(bot: AeBot, client: SithClient) -> AppRunner:
    """Start the web server to authenticate users through the student website."""
    app = Application()

    app["auth-service"] = AuthService(bot, client)
    app.add_routes(
        [
            post("/callback/{user_id}/", login_callback),
        ]
    )
    runner = AppRunner(app)
    await runner.setup()
    site = TCPSite(runner, "0.0.0.0", 8001)
    await site.start()
    return runner
