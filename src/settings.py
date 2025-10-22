from pathlib import Path
from typing import Literal

from pydantic import BaseModel, HttpUrl, SecretStr
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

BASE_DIR = Path(__file__).resolve().parent.parent


class ApiConfig(BaseModel):
    url: HttpUrl = "http://127.0.0.1:8000/"
    api_key: SecretStr


class GuildConfig(BaseModel):
    id: int
    news_channel_id: int | None = None
    news_role_id: int | None = None
    auto_role_channel_id: int | None = None


class BotConfig(BaseModel):
    token: SecretStr
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "FATAL", "CRITICAL"] = (
        "INFO"
    )
    command_prefix: str = "/"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        toml_file=str(BASE_DIR / "bot.toml"),
        env_nested_delimiter="__",
    )

    bot: BotConfig
    guild: GuildConfig
    sith_api: ApiConfig

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Define the priority for different sources of configuration.

        The configuration is loaded from the following sources
        (in descending order of priority) :

            1. Arguments passed to the Settings class initialiser.
            2. Variables loaded from the `bot.toml` file
            3. The default field values for the Settings model.
        """
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls),
        )
