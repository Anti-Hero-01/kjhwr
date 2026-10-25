from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Gridbricks Wind Intelligence"
    demo_mode: bool = True
    elexon_base_url: str = "https://data.elexon.co.uk/bmrs/api/v1"
    decision_cutoff: str = "10:00"
    timezone: str = "Europe/London"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
