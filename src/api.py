
import datetime
import logging
from decimal import Decimal
from typing import Optional

import fastapi
from sqlmodel import Session, select

from .db import Album, Artist, create_db, get_session

app = fastapi.FastAPI(
    openapi_url="/openapi.json",
    docs_url="/docs",
)
logging.basicConfig(level=logging.INFO)


@app.on_event("startup")
def on_startup():
    create_db()


@app.get("/")
def read_root():
    return {"Hello": "World"}



@app.get("/artists", response_model=list[Artist])
async def list_artists(*, session: Session = fastapi.Depends(get_session)):
    return session.exec(select(Artist)).all()


@app.get("/artist/{artist_id}/albums", response_model=list[Album])
async def get_albums(
    artist_id: int,
    price_gte: Optional[Decimal] = None,
    price_lte: Optional[Decimal] = None,
    date_gte: Optional[datetime.date] = None,
    date_lte: Optional[datetime.date] = None,
    include_tracks: bool = False,
    session: Session = fastapi.Depends(get_session)
):
    if price_gte and price_lte and price_gte > price_lte:
        raise fastapi.HTTPException(
            status_code=400, 
            detail='price_gte must be less than price_lte'
        )
    if date_gte and date_lte and date_gte > date_lte:
        raise fastapi.HTTPException(
            status_code=400, 
            detail='date_gte must be less than date_lte'
        )

    # TODO: consider erroring if artist doesn't exist
    q = (select(Album)
        .where(Album.artist_id == artist_id)
    )

    if price_gte:
        q = q.where(Album.price >= price_gte)
    if price_lte:
        q = q.where(Album.price <= price_lte)
    if date_gte:
        q = q.where(Album.release_date >= date_gte)
    if date_lte:
        q = q.where(Album.release_date <= date_lte)

    albums = session.exec(q).all()
    # Hack—better to do this in select with load_only, but hitting some SQLAlchemy nonsense.
    if not include_tracks:
        for a in albums:
            del a.tracks
    return albums



@app.post("/artists", response_model=Artist)
async def create_artist(artist: Artist, session: Session = fastapi.Depends(get_session)):
    if artist.id is not None:
        raise fastapi.HTTPException(
            status_code=400, 
            detail='Cannot supply id'
        )
    
    if artist.albums:
        raise fastapi.HTTPException(
            status_code=400, 
            detail='Cannot create albums with this endpoint'
        )


    session.add(artist)
    session.commit()
    session.refresh(artist)
    return artist


@app.post("/artist/{artist_id}/albums", response_model=Album)
async def create_album(album: Album, session: Session = fastapi.Depends(get_session)):
    if album.id is not None:
        raise fastapi.HTTPException(
            status_code=400, 
            detail='Cannot supply id'
        )
    if album.artist:
        # Make sure you can't override an existing artist
        raise fastapi.HTTPException(
            status_code=400, 
            detail='Cannot create artist with this endpoint'
        )

    session.add(album)
    session.commit()
    session.refresh(album)
    return album
