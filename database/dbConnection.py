from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

from config.app_logger import logger
from config.config import settings
from models.user import User
from routers.secrect.authcationAndTokenCreation import decodeAccessToken
from models.user import Role

engine = create_engine(settings.DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_database_if_missing():
    database_url = make_url(settings.DB_URL)
    if database_url.get_backend_name() != "postgresql":
        return

    database_name = database_url.database
    if not database_name:
        raise RuntimeError("DB_URL must include a PostgreSQL database name")

    import psycopg
    from psycopg import sql

    admin_url = database_url.set(database="postgres")
    try:
        with psycopg.connect(
            admin_url.render_as_string(hide_password=False),
            autocommit=True,
        ) as connection:
            exists = connection.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (database_name,)
            ).fetchone()
            if exists is None:
                try:
                    connection.execute(
                        sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name))
                    )
                    logger.info("Created PostgreSQL database '%s'", database_name)
                except psycopg.errors.DuplicateDatabase:
                    logger.info("PostgreSQL database '%s' was created by another worker", database_name)
            else:
                logger.info("PostgreSQL database '%s' already exists", database_name)
    except Exception:
        logger.exception("Could not create or connect to PostgreSQL database '%s'", database_name)
        raise


def commit_with_logging(db, operation: str) -> None:
    """Commit a session, rolling it back and logging details on failure."""
    try:
        db.commit()
    except SQLAlchemyError as exc:
        try:
            db.rollback()
        except SQLAlchemyError:
            logger.exception("Rollback also failed after attempting to %s", operation)
        logger.error(
            "Database operation failed while attempting to %s",
            operation,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        raise


def flush_with_logging(db, operation: str) -> None:
    """Flush a session, rolling it back and logging details on failure."""
    try:
        db.flush()
    except SQLAlchemyError as exc:
        try:
            db.rollback()
        except SQLAlchemyError:
            logger.exception("Rollback also failed after attempting to %s", operation)
        logger.error(
            "Database operation failed while attempting to %s",
            operation,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        raise

oauth2Scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def getDb():
    try:
        db = SessionLocal()
    except Exception:
        logger.exception("Could not open a database session")
        raise
    try:
        yield db
    finally:
        try:
            db.close()
        except Exception:
            logger.exception("Could not close a database session")
            raise


def getCurrentUser(token: str = Depends(oauth2Scheme), db=Depends(getDb)):
   
    payload = decodeAccessToken(token)
    email = payload.get("sub") if payload else None
    if not email:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user


def require_admin(current_user=Depends(getCurrentUser)):
    

    if current_user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
