from pydantic_settings import BaseSettings, SettingsConfigDict
from google import genai
from urllib.parse import quote_plus

class GeminiSettings(BaseSettings):
    GOOGLE_API_KEY: str
    MODEL_NAME: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
        )
    
    def __init__(self, **data):
        super().__init__(**data)
        self.CLIENT=genai.Client(api_key=self.GOOGLE_API_KEY)


class DatabaseSettings(BaseSettings):
    """
    PostgreSQL / Cloud SQL database configuration.

    Manages connection parameters for the PostgreSQL database and constructs
    the DSN (Data Source Name) string for asyncpg connections.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    DB_USER_SQL: str
    DB_PASSWORD_SQL: str
    DB_NAME_SQL: str
    DB_HOST_SQL: str
    DB_PORT_SQL: int = 5432

    @property
    def dsn(self) -> str:
        """
        Construct the complete PostgreSQL DSN string (asyncpg format).
        Returns:
            str: PostgreSQL connection string
        """
        encoded_password = quote_plus(self.DB_PASSWORD_SQL)

        if self.DB_HOST_SQL.startswith("/"):
            dsn = f"postgresql://{self.DB_USER_SQL}:{encoded_password}@/{self.DB_NAME_SQL}?host={self.DB_HOST_SQL}"
        else:
            dsn = f"postgresql://{self.DB_USER_SQL}:{encoded_password}@{self.DB_HOST_SQL}:{self.DB_PORT_SQL}/{self.DB_NAME_SQL}"

        return dsn

gemini_settings = GeminiSettings()
database_settings = DatabaseSettings()  # type: ignore



