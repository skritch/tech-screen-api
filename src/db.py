import datetime
import json
from typing import Optional
from decimal import Decimal
import pydantic
from sqlmodel import JSON, Column, Field, Relationship, Session, SQLModel, String, create_engine
from .settings import DB_URL
from sqlalchemy.future import Engine


money = Decimal()

class Artist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # TODO: unique?
    name: str
    albums: Optional[list["Album"]] = Relationship(back_populates='artist')

# Not a table, just using as JSON column for now.
class Track(pydantic.BaseModel):
    title: Optional[str]
    duration_ms: Optional[int]


class Album(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    artist_id: Optional[int] = Field(default=None, foreign_key="artist.id", index=True)
    artist: Artist = Relationship(back_populates='albums')

    # TODO: Unique per artist?
    name: str
    release_date: datetime.date
    price: Decimal

    tracks: Optional[list[Track]] = Field(default=None, sa_column=Column(JSON))

    @pydantic.validator('tracks')
    def val_track(cls, val):
        if val is not None:
            return [t.dict() for t in val]


db: Engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False}
)

def create_db():
    SQLModel.metadata.create_all(db)

def get_session():
    with Session(db) as session:
        yield session

if __name__ == '__main__':
    create_db()
