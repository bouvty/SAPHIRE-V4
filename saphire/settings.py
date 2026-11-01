from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    discord_token: str = ""
    discord_prefix: str = ";"
    discord_stream_name: str = "Saphire | Discord Members"
    discord_stream_url: str = "https://www.twitch.tv/discord"
    embed_color: str = "0x000000"
    clear_console_on_ready: bool = True
    log_timezone: str = "Europe/London"
    database_url: str = ""
    enable_discord_bot: bool = True
    enable_stock_sync: bool = True
    stock_source_url: str = "https://176.100.37.219/api/v2/stock"
    stock_refresh_seconds: int = 300
    stock_request_timeout_seconds: int = 20
    panel_refresh_seconds: int = 15
    port: int = 8000
    @property
    def color(self) -> int:
        return int(self.embed_color, 0)
settings = Settings()
