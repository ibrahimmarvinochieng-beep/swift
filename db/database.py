import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from utils.config_loader import get_settings

settings = get_settings()

db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

connect_args: dict = {}
if settings.db_sslmode in ("require", "verify-ca", "verify-full"):
    ssl_ctx = ssl.create_default_context()
    if settings.db_sslmode in ("verify-ca", "verify-full"):
        ssl_ctx.load_verify_locations(settings.tls_ca_file)
    else:
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_ctx

engine = create_async_engine(
    db_url,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    echo=settings.environment == "development",
    connect_args=connect_args,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
