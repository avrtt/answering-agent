from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from models import Base
from config import settings
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._setup_database()
    
    def _setup_database(self):
        """Setup database connection and create tables"""
        try:
            # Create engine
            if settings.DATABASE_URL.startswith("sqlite"):
                self.engine = create_engine(
                    settings.DATABASE_URL,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                )
            else:
                self.engine = create_engine(settings.DATABASE_URL)
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database setup completed successfully")
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    def close_session(self, session: Session):
        """Close a database session"""
        if session:
            session.close()


# Global database manager instance
db_manager = DatabaseManager()


def get_db():
    """Dependency to get database session"""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db_manager.close_session(db)
