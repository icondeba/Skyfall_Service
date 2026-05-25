from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./skyfall_local.db"

    SECRET_KEY: str = "dev-only-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    AUTH_DISABLED: bool = True

    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    UPI_VPA: str = ""
    UPI_PAYEE_NAME: str = "Skyfall Lounge"

    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_REALTIME_CHANNEL: str = "skyfall-lounge"

    META_WA_TOKEN: str = ""
    META_WA_PHONE_ID: str = ""

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Skyfall Lounge"

    REDIS_URL: str = ""

    CAFE_NAME: str = "Skyfall Lounge"
    CAFE_ADDRESS: str = ""
    CAFE_GSTIN: str = ""
    CAFE_PHONE: str = ""
    CAFE_SOCIAL_HANDLES: str = "@skyfalllounge"
    APP_NAME: str = "Skyfall Lounge API"
    ENVIRONMENT: str = "development"
    FRONTEND_LOCAL_ORIGIN: str = "http://localhost:3000"
    FRONTEND_PRODUCTION_ORIGIN: str = "https://skyfall-lounge.example.com"
    CORS_ORIGINS: str = Field(default="http://localhost:3000,https://skyfall-lounge.example.com")
    CURRENCY: str = "INR"
    TAX_RATE: float = 0.05

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

    @property
    def app_name(self) -> str:
        return self.APP_NAME

    @property
    def environment(self) -> str:
        return self.ENVIRONMENT

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def tax_rate(self) -> float:
        return self.TAX_RATE

    @property
    def currency(self) -> str:
        return self.CURRENCY

    @property
    def auth_disabled(self) -> bool:
        return self.AUTH_DISABLED

    @property
    def razorpay_key_id(self) -> str:
        return self.RAZORPAY_KEY_ID

    @property
    def razorpay_key_secret(self) -> str:
        return self.RAZORPAY_KEY_SECRET

    @property
    def razorpay_webhook_secret(self) -> str:
        return self.RAZORPAY_WEBHOOK_SECRET

    @property
    def supabase_url(self) -> str:
        return self.SUPABASE_URL

    @property
    def supabase_anon_key(self) -> str:
        return self.SUPABASE_ANON_KEY

    @property
    def supabase_service_role_key(self) -> str:
        return self.SUPABASE_SERVICE_KEY

    @property
    def supabase_realtime_channel(self) -> str:
        return self.SUPABASE_REALTIME_CHANNEL

    @property
    def allowed_origins(self) -> list[str]:
        origins = [
            self.FRONTEND_LOCAL_ORIGIN,
            self.FRONTEND_PRODUCTION_ORIGIN,
            *[
                origin.strip()
                for origin in self.CORS_ORIGINS.split(",")
                if origin.strip()
            ],
        ]
        return list(dict.fromkeys(origin for origin in origins if origin))

    @property
    def supabase_broadcast_url(self) -> str | None:
        if not self.SUPABASE_URL:
            return None
        return f"{self.SUPABASE_URL.rstrip('/')}/realtime/v1/api/broadcast"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
