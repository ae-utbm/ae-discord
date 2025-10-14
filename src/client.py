import asyncio
import logging
import types
from datetime import date, datetime

from aiohttp import (
    ClientSession,
    TraceConfig,
    TraceRequestEndParams,
    TraceRequestStartParams,
)
from pydantic import BaseModel, ValidationError

from src.settings import Settings


class UserSchema(BaseModel):
    id: int
    nick_name: str | None
    first_name: str
    last_name: str


class MembershipSchema(BaseModel):
    user: UserSchema
    start_date: date
    end_date: date | None
    role: int
    description: str


class ClubSchema(BaseModel):
    id: int
    name: str
    logo: str | None
    is_active: bool
    short_description: str
    address: str
    members: list[MembershipSchema]


class SimpleClubSchema(BaseModel):
    id: int
    name: str


class ClubProfileSchema(SimpleClubSchema):
    logo: str | None = None
    url: str


class ClubSearchResultSchema(BaseModel):
    count: int
    results: list[SimpleClubSchema]


class NewsSchema(BaseModel):
    id: int
    title: str
    summary: str
    is_published: bool
    club: ClubProfileSchema
    url: str


class NewsDateSchema(BaseModel):
    id: int
    start_date: datetime
    end_date: datetime
    news: NewsSchema


class NewsDateResultSchema(BaseModel):
    count: int
    results: list[NewsDateSchema]


class SithClient(ClientSession):
    def __init__(self):
        self.logger = logging.getLogger("sith")
        config = Settings().sith_api
        trace_config = TraceConfig()
        trace_config.on_request_start.append(request_logging_start)
        trace_config.on_request_end.append(request_logging_end)
        super().__init__(
            base_url=str(config.url),
            headers={"X-APIKey": config.api_key.get_secret_value()},
            trace_configs=[trace_config],
        )

    async def get_club(self, club_id: int) -> ClubSchema | None:
        """Fetch the information about the club from the sith API."""
        async with self.get(f"/api/club/{club_id}") as res:
            content = await res.read()
        try:
            return ClubSchema.model_validate_json(content)
        except ValidationError as e:
            self.logger.error(str(e))

    async def search_clubs(self, search: str) -> list[SimpleClubSchema] | None:
        """Given a string, get the result of the autocompletion route of the API."""
        if len(search) < 1:
            # The sith API search requires a string with a min length of 1
            return None
        async with self.get("/api/club/search", params={"search": search}) as res:
            content = await res.read()
        try:
            return ClubSearchResultSchema.model_validate_json(content).results
        except ValidationError as e:
            self.logger.error(str(e))

    async def search_news(
        self, after: datetime | None = None, before: datetime | None = None
    ) -> list[NewsDateSchema] | None:
        params = {"is_published": "true"}
        if after:
            params["after"] = after.isoformat()
        if before:
            params["before"] = before.isoformat()
        async with self.get("/api/news/date", params=params) as res:
            content = await res.read()
        try:
            return NewsDateResultSchema.model_validate_json(content).results
        except ValidationError as e:
            self.logger.error(str(e))


async def request_logging_start(
    _session: SithClient,
    trace_config_ctx: types.SimpleNamespace,
    _params: TraceRequestStartParams,
):
    """Use the tracing features of aiohttp to log the issued requests.

    Used in conjunction with `request_logging_end`.
    """
    trace_config_ctx.start = asyncio.get_event_loop().time()


async def request_logging_end(
    session: SithClient,
    trace_config_ctx: types.SimpleNamespace,
    params: TraceRequestEndParams,
):
    """Use the tracing features of aiohttp to log the issued requests.

    Used in conjunction with `request_logging_start`.
    """
    elapsed = asyncio.get_event_loop().time() - trace_config_ctx.start
    session.logger.info(
        f"request {params.url} "
        f"({params.response.status} {params.response.reason}) "
        f"[{elapsed:.6f}sec]"
    )
