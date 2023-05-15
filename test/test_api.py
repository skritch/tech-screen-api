import pytest
from src.api import app
from src.api import get_session

import datetime
import json
from typing import Optional
from decimal import Decimal
import pydantic
from sqlmodel import JSON, Column, Field, Relationship, Session, SQLModel, String, create_engine
from sqlalchemy.future import Engine
from sqlalchemy.pool import StaticPool

from fastapi.testclient import TestClient
from copy import deepcopy

TEST_DB_URL = 'sqlite://'

test_db: Engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool  # Needed for in-memory SQLite so that test threads share the same DB
)

@pytest.fixture
def create_db():
    SQLModel.metadata.drop_all(test_db, checkfirst=True)
    SQLModel.metadata.create_all(test_db)
    

def override_get_session():
    with Session(test_db) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session
client = TestClient(app)


artist_1 = {'name': 'the first ones'}
artist_2 = {'name': 'number two'}
album_1 = {
  "artist_id": 1,
  "name": "the first part",
  "release_date": "2023-05-15",
  "price": 50,
}
album_2 = {
  "artist_id": 1,
  "name": "the second part",
  "release_date": "2023-06-01",
  "price": 100,
  "tracks": [
    {
      "title": "intro",
      "duration_ms": 400
    },
    {
      "title": "the body of the work",
      "duration_ms": 400000
    }
  ]
}


@pytest.mark.usefixtures("create_db")
def test_artists():
    list_response_before = client.get('/artists/')
    assert list_response_before.status_code == 200, list_response_before.text
    assert list_response_before.json() == []

    for (idx, artist) in enumerate([artist_1, artist_2]):
        create_response = client.post('/artists/', json=artist)
        assert create_response.status_code == 200, create_response.text
        assert create_response.json() == {'id': idx + 1, 'name': artist['name']}

    list_response_after = client.get('/artists/')
    assert list_response_after.status_code == 200, list_response_after.text
    assert list_response_after.json() == [{'id': 1, 'name': artist_1['name']}, {'id': 2, 'name': artist_2['name']}]


@pytest.mark.usefixtures("create_db")
def test_albums():
    client.post('/artists/', json=artist_1)

    albums_response_before = client.get('/artist/1/albums')
    assert albums_response_before.status_code == 200, albums_response_before.text
    assert albums_response_before.json() == []

    for (idx, album) in enumerate([album_1, album_2]):
        create_response = client.post('/artist/1/albums/', json=album)
        assert create_response.status_code == 200, create_response.text
        expected = deepcopy(album)
        expected['id'] = idx + 1
        if 'tracks' not in expected:
          expected['tracks'] = None
        assert create_response.json() == expected

    get_albums_response_no_tracks = client.get('artist/1/albums')
    assert get_albums_response_no_tracks.status_code == 200, get_albums_response_no_tracks.text
    expected = [deepcopy(album_1), deepcopy(album_2)]
    expected[0].update({'id': 1, 'tracks': None, 'price': 50.0})
    expected[1].update({'id': 2, 'tracks': None, 'price': 100.0})
    assert get_albums_response_no_tracks.json() == expected

    get_albums_response_tracks = client.get('artist/1/albums?include_tracks=1')
    assert get_albums_response_tracks.status_code == 200, get_albums_response_tracks.text
    expected = [deepcopy(album_1), deepcopy(album_2)]
    expected[0].update({'id': 1, 'tracks': None, 'price': 50.0})
    expected[1].update({'id': 2, 'price': 100.0})
    assert get_albums_response_tracks.json() == expected

    get_albums_response_filter_price = client.get('artist/1/albums?price_gte=75')
    assert get_albums_response_filter_price.status_code == 200, get_albums_response_filter_price.text
    expected = [deepcopy(album_2)]
    expected[0].update({'id': 2, 'price': 100.0, 'tracks': None})
    assert get_albums_response_filter_price.json() == expected

    get_albums_response_filter_date = client.get('artist/1/albums?date_gte=2023-05-25')
    assert get_albums_response_filter_date.status_code == 200, get_albums_response_filter_date.text
    expected = [deepcopy(album_2)]
    expected[0].update({'id': 2, 'price': 100.0, 'tracks': None})
    assert get_albums_response_filter_date.json() == expected

    get_albums_response_bad_price_filter = client.get('artist/1/albums?price_gte=75&price_lte=50')
    assert get_albums_response_bad_price_filter.status_code == 400

    get_albums_response_bad_date_filter = client.get('artist/1/albums?date_gte=2023-05-25&date_lte=2023-05-15')
    assert get_albums_response_bad_date_filter.status_code == 400