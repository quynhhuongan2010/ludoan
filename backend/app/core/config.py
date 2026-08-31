from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MYSQL_HOST: str
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str

    # Neu khai bao san bien DATABASE_URL trong .env thi dung nguyen chuoi do
    # (phai tu ma hoa ky tu dac biet, vd @ -> %40). De trong -> tu build tu cac
    # bien MYSQL_* o tren, tu dong ma hoa an toan bang quote_plus.
    DATABASE_URL_ENV: str = Field(default="", alias="DATABASE_URL")

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # Upload file (anh thumbnail, tai lieu .pdf/.docx...)
    UPLOAD_DIR: str = "storage/uploads"
    MAX_UPLOAD_MB: int = 25

    # CORS: cho phep them cac origin co dinh, ngoai regex localhost/LAN o main.py
    EXTRA_CORS_ORIGINS: str = ""

    # Tai khoan admin he thong tao san khi DB chua co tai khoan `is_system` nao.
    # Doc tu .env; co gia tri mac dinh - chu don vi doi lai sau lan dang nhap dau.
    SYSTEM_ADMIN_USERNAME: str = "admin"
    SYSTEM_ADMIN_PASSWORD: str = "admin"

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", populate_by_name=True
    )

    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_URL_ENV:
            url = self.DATABASE_URL_ENV
            if "charset=" not in url:
                url += ("&" if "?" in url else "?") + "charset=utf8mb4"
            return url
        user = quote_plus(self.MYSQL_USER)
        password = quote_plus(self.MYSQL_PASSWORD)
        return (
            f"mysql+pymysql://{user}:{password}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"
        )

    @property
    def upload_path(self) -> Path:
        path = Path(self.UPLOAD_DIR)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent.parent.parent / path
        return path

    @property
    def extra_cors_list(self) -> list[str]:
        return [o.strip() for o in self.EXTRA_CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
