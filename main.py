# Movie REST API - Backend Development, Week 3 (Python + FastAPI)
# Port of the Week 2 Express API: same resource, same CRUD operations.
from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(
    title="Movie API",
    description="Week 3: the Express Movie API ported to FastAPI.",
    version="1.0.0",
)

MAX_YEAR = date.today().year + 5


# ---------- Pydantic models ----------

class MovieCreate(BaseModel):
    """Data the client sends for POST and PUT (all fields required)."""

    # Remove extra spaces from strings, so "   " counts as empty
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, examples=["Arrival"])
    # strict=True: "2016" (text) is rejected, only a real integer is accepted
    year: int = Field(ge=1888, le=MAX_YEAR, strict=True, examples=[2016])
    genre: str = Field(min_length=1, examples=["Sci-Fi"])


class MovieUpdate(BaseModel):
    """Data the client sends for PATCH (every field is optional)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1)
    year: int | None = Field(default=None, ge=1888, le=MAX_YEAR, strict=True)
    genre: str | None = Field(default=None, min_length=1)


class Movie(BaseModel):
    """A movie as the API returns it (includes the id)."""

    id: int
    title: str
    year: int
    genre: str


# ---------- Data (in memory, like in Express) ----------

movies: list[dict] = [
    {"id": 1, "title": "Inception", "year": 2010, "genre": "Sci-Fi"},
    {"id": 2, "title": "The Matrix", "year": 1999, "genre": "Sci-Fi"},
    {"id": 3, "title": "Parasite", "year": 2019, "genre": "Thriller"},
]
next_id = 4  # the server creates the ids


def find_movie(movie_id: int) -> dict:
    """Return the movie or raise 404 Not Found."""
    for movie in movies:
        if movie["id"] == movie_id:
            return movie
    raise HTTPException(status_code=404, detail="Movie not found")


# ---------- Routes ----------

@app.get("/")
def root():
    return {"message": "Hello from FastAPI"}


@app.get("/movies", response_model=list[Movie])
def get_movies(
    genre: str | None = None,
    min_year: int | None = None,
    sort: Literal["year", "title"] | None = None,
):
    """List movies. Optional filters: genre, min_year. Optional sort: year or title."""
    result = list(movies)  # copy, so the original list is not changed

    if genre is not None:
        result = [m for m in result if m["genre"].lower() == genre.lower()]

    if min_year is not None:
        result = [m for m in result if m["year"] >= min_year]

    if sort == "year":
        result = sorted(result, key=lambda m: m["year"])
    elif sort == "title":
        result = sorted(result, key=lambda m: m["title"].lower())

    return result


@app.get("/movies/{movie_id}", response_model=Movie)
def get_movie(movie_id: int):
    return find_movie(movie_id)


@app.post("/movies", response_model=Movie, status_code=status.HTTP_201_CREATED)
def create_movie(movie: MovieCreate):
    global next_id
    new_movie = {"id": next_id, **movie.model_dump()}
    next_id += 1
    movies.append(new_movie)
    return new_movie


@app.put("/movies/{movie_id}", response_model=Movie)
def replace_movie(movie_id: int, movie: MovieCreate):
    existing = find_movie(movie_id)
    # Replace all editable fields, keep the id
    existing.update(movie.model_dump())
    return existing


@app.patch("/movies/{movie_id}", response_model=Movie)
def update_movie(movie_id: int, movie: MovieUpdate):
    existing = find_movie(movie_id)

    # Only the fields the client actually sent
    changes = movie.model_dump(exclude_unset=True)

    # Sending null (e.g. {"title": null}) would remove a required value
    for field, value in changes.items():
        if value is None:
            raise HTTPException(status_code=422, detail=f"{field} cannot be null")

    existing.update(changes)
    return existing


@app.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int):
    movie = find_movie(movie_id)
    movies.remove(movie)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
