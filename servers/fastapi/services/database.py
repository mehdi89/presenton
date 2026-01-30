from collections.abc import AsyncGenerator
import os
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy import text, inspect
from sqlmodel import SQLModel

from models.sql.async_presentation_generation_status import (
    AsyncPresentationGenerationTaskModel,
)
from models.sql.image_asset import ImageAsset
from models.sql.key_value import KeyValueSqlModel
from models.sql.ollama_pull_status import OllamaPullStatus
from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel
from models.sql.presentation_layout_code import PresentationLayoutCodeModel
from models.sql.template import TemplateModel
from models.sql.webhook_subscription import WebhookSubscription
from utils.db_utils import get_database_url_and_connect_args


database_url, connect_args = get_database_url_and_connect_args()

sql_engine: AsyncEngine = create_async_engine(database_url, connect_args=connect_args)
async_session_maker = async_sessionmaker(sql_engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# Container DB (Lives inside the container)
container_db_url = "sqlite+aiosqlite:////app/container.db"
container_db_engine: AsyncEngine = create_async_engine(
    container_db_url, connect_args={"check_same_thread": False}
)
container_db_async_session_maker = async_sessionmaker(
    container_db_engine, expire_on_commit=False
)


async def get_container_db_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with container_db_async_session_maker() as session:
        yield session


# Create Database and Tables
async def create_db_and_tables():
    async with sql_engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: SQLModel.metadata.create_all(
                sync_conn,
                tables=[
                    PresentationModel.__table__,
                    SlideModel.__table__,
                    KeyValueSqlModel.__table__,
                    ImageAsset.__table__,
                    PresentationLayoutCodeModel.__table__,
                    TemplateModel.__table__,
                    WebhookSubscription.__table__,
                    AsyncPresentationGenerationTaskModel.__table__,
                ],
            )
        )

    async with container_db_engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: SQLModel.metadata.create_all(
                sync_conn,
                tables=[OllamaPullStatus.__table__],
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
