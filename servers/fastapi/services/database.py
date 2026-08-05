from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy import text, inspect, event, or_
from sqlalchemy.orm import Session, with_loader_criteria
from sqlmodel import SQLModel

from models.sql.async_task import AsyncTaskModel
from models.sql.async_presentation_generation_status import (
    AsyncPresentationGenerationTaskModel,
)
from models.sql.chat_history_message import ChatHistoryMessageModel
from models.sql.font_upload import FontUpload
from models.sql.image_asset import ImageAsset
from models.sql.key_value import KeyValueSqlModel
from models.sql.ollama_pull_status import OllamaPullStatus
from models.sql.presentation_layout_code import PresentationLayoutCodeModel
from models.sql.presentation import PresentationModel
from models.sql.template import TemplateModel
from models.sql.template_create_info import TemplateCreateInfoModel
from models.sql.template_v2 import TemplateV2
from models.sql.slide import SlideModel
from models.sql.webhook_subscription import WebhookSubscription
from models.sql.user import User
from models.sql.access_token import AccessToken
from models.sql.provider_settings import ProviderSettings
from api.v1.auth.context import get_current_owner_id
from utils.get_env import get_migrate_database_on_startup_env
from utils.db_utils import get_database_url_and_connect_args, get_pool_kwargs


database_url, connect_args = get_database_url_and_connect_args()

# Apply connection-pool settings for server-class databases (PostgreSQL, MySQL).
# SQLite uses a file-lock model and ignores pool configuration, so we skip it.
_pool_kwargs = get_pool_kwargs() if "sqlite" not in database_url else {}

sql_engine: AsyncEngine = create_async_engine(
    database_url, connect_args=connect_args, **_pool_kwargs
)


if "sqlite" in database_url:
    @event.listens_for(sql_engine.sync_engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


async_session_maker = async_sessionmaker(sql_engine, expire_on_commit=False)


_STRICT_OWNER_MODELS = (
    PresentationModel,
    SlideModel,
    PresentationLayoutCodeModel,
    TemplateModel,
    ChatHistoryMessageModel,
    ImageAsset,
    TemplateCreateInfoModel,
    AsyncTaskModel,
    AsyncPresentationGenerationTaskModel,
    WebhookSubscription,
)


@event.listens_for(Session, "do_orm_execute")
def _scope_owned_selects(execute_state) -> None:
    """Apply tenant criteria to every ORM SELECT performed during a request."""
    owner_id = get_current_owner_id()
    if (
        owner_id is None
        or not execute_state.is_select
        or execute_state.execution_options.get("skip_owner_scope")
    ):
        return

    statement = execute_state.statement
    for model in _STRICT_OWNER_MODELS:
        statement = statement.options(
            with_loader_criteria(
                model,
                lambda row: row.owner_id == owner_id,
                include_aliases=True,
            )
        )
    statement = statement.options(
        with_loader_criteria(
            TemplateV2,
            lambda row: or_(
                row.owner_id == owner_id,
                (row.owner_id.is_(None) & row.is_default.is_(True)),
            ),
            include_aliases=True,
        )
    )
    execute_state.statement = statement


@event.listens_for(Session, "before_flush")
def _stamp_new_owned_rows(session, _flush_context, _instances) -> None:
    owner_id = get_current_owner_id()
    if owner_id is None:
        return
    owner_models = _STRICT_OWNER_MODELS + (TemplateV2,)
    for instance in session.new:
        if isinstance(instance, owner_models):
            instance.owner_id = owner_id


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# Create Database and Tables
async def create_db_and_tables():
    should_run_alembic = get_migrate_database_on_startup_env() in ["true", "True"]
    if not should_run_alembic:
        async with sql_engine.begin() as conn:
            await conn.run_sync(
                lambda sync_conn: SQLModel.metadata.create_all(
                    sync_conn,
                    tables=[
                        PresentationModel.__table__,
                        SlideModel.__table__,
                        KeyValueSqlModel.__table__,
                        TemplateV2.__table__,
                        ChatHistoryMessageModel.__table__,
                        ImageAsset.__table__,
                        FontUpload.__table__,
                        PresentationLayoutCodeModel.__table__,
                        TemplateCreateInfoModel.__table__,
                        TemplateModel.__table__,
                        WebhookSubscription.__table__,
                        AsyncTaskModel.__table__,
                        AsyncPresentationGenerationTaskModel.__table__,
                        OllamaPullStatus.__table__,
                        User.__table__,
                        AccessToken.__table__,
                        ProviderSettings.__table__,
                    ],
                )
            )

    # Run automatic migrations for new columns
    await run_migrations()


async def run_migrations():
    """
    Run automatic database migrations to add missing columns.
    This ensures new columns are added when the code is deployed to production.
    """
    async with sql_engine.begin() as conn:
        await conn.run_sync(_migrate_presentations_table)


def _migrate_presentations_table(sync_conn):
    """
    Add missing columns to the presentations table.
    This is called synchronously within an async context.
    """
    inspector = inspect(sync_conn)

    # Check if presentations table exists
    if not inspector.has_table("presentations"):
        print("[Migration] presentations table does not exist yet, skipping column migration")
        return

    # Get existing columns
    existing_columns = {col["name"] for col in inspector.get_columns("presentations")}

    # Define new columns that need to be added
    # Format: (column_name, column_type_sql)
    # Use appropriate SQL type based on database dialect
    dialect_name = sync_conn.dialect.name

    if dialect_name == "sqlite":
        column_type = "TEXT"
    elif dialect_name == "postgresql":
        column_type = "VARCHAR"
    elif dialect_name == "mysql":
        column_type = "VARCHAR(255)"
    else:
        column_type = "VARCHAR(255)"

    new_columns = [
        ("tubeonai_auth_token", column_type),
        ("tubeonai_user_id", column_type),
        ("tubeonai_source_id", column_type),
        ("tubeonai_source_type", column_type),
        ("tubeonai_provider_model_id", column_type),
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            print(f"[Migration] Adding column: presentations.{col_name}")
            try:
                sync_conn.execute(
                    text(f"ALTER TABLE presentations ADD COLUMN {col_name} {col_type}")
                )
            except Exception as e:
                # Column might already exist in some edge cases
                print(f"[Migration] Warning adding column {col_name}: {e}")
        else:
            print(f"[Migration] Column already exists: presentations.{col_name}")


async def dispose_engines():
    """Dispose all engine connection pools.

    Call this during application shutdown (e.g. in a FastAPI ``shutdown``
    event or lifespan context) to release every connection back to the
    database and prevent stale / leaked connections.
    """
    await sql_engine.dispose()
