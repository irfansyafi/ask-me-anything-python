from datetime import datetime

from sqlalchemy import Column, String

from core.database import Base, engine, malaysia_tz


class Question(Base):
    __tablename__ = "questions"
    id = Column(String, primary_key=True, index=True)
    content = Column(String, index=True)
    answer = Column(String, nullable=True)
    timestamp = Column(
        String, default=lambda: datetime.now(malaysia_tz).strftime("%d-%m-%Y %H:%M:%S")
    )


# Ensure tables are created when models are loaded
Base.metadata.create_all(bind=engine)
