from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, text
from sqlalchemy.orm import selectinload
from bot.database.models import (
    Movie, MovieVersion, Episode, EpisodeVersion,
    SavedMovie, DownloadLog
)
from datetime import datetime, date


class MovieService:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ─── Fetch ────────────────────────────────────────────────────────────────

    async def get_by_code(self, code: str) -> Optional[Movie]:
        result = await self.session.execute(
            select(Movie)
            .where(Movie.code == code, Movie.is_active == True)
            .options(
                selectinload(Movie.versions),
                selectinload(Movie.episodes).selectinload(Episode.versions),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, movie_id: int) -> Optional[Movie]:
        result = await self.session.execute(
            select(Movie)
            .where(Movie.id == movie_id, Movie.is_active == True)
            .options(
                selectinload(Movie.versions),
                selectinload(Movie.episodes).selectinload(Episode.versions),
            )
        )
        return result.scalar_one_or_none()

    async def get_version(self, version_id: int) -> Optional[MovieVersion]:
        result = await self.session.execute(
            select(MovieVersion).where(
                MovieVersion.id == version_id,
                MovieVersion.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_episode_version(self, version_id: int) -> Optional[EpisodeVersion]:
        result = await self.session.execute(
            select(EpisodeVersion).where(
                EpisodeVersion.id == version_id,
                EpisodeVersion.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_versions(self, movie_id: int) -> List[MovieVersion]:
        result = await self.session.execute(
            select(MovieVersion).where(
                MovieVersion.movie_id == movie_id,
                MovieVersion.is_active == True,
            )
        )
        return result.scalars().all()

    async def get_episode_active_versions(self, episode_id: int) -> List[EpisodeVersion]:
        result = await self.session.execute(
            select(EpisodeVersion).where(
                EpisodeVersion.episode_id == episode_id,
                EpisodeVersion.is_active == True,
            )
        )
        return result.scalars().all()

    # ─── Search ───────────────────────────────────────────────────────────────

    async def search_by_code(self, code: str) -> Optional[Movie]:
        result = await self.session.execute(
            select(Movie).where(Movie.code == code, Movie.is_active == True)
        )
        return result.scalar_one_or_none()

    async def search_exact(self, query: str, limit: int = 10) -> List[Movie]:
        """Exact ILIKE search across all title fields."""
        result = await self.session.execute(
            select(Movie).where(
                Movie.is_active == True,
                or_(
                    Movie.title_original.ilike(f"%{query}%"),
                    Movie.title_uz.ilike(f"%{query}%"),
                    Movie.title_ru.ilike(f"%{query}%"),
                    Movie.title_en.ilike(f"%{query}%"),
                    Movie.actors.ilike(f"%{query}%"),
                    Movie.genre.ilike(f"%{query}%"),
                    Movie.keywords.ilike(f"%{query}%"),
                )
            ).limit(limit)
        )
        return result.scalars().all()

    async def search_fuzzy(self, query: str, limit: int = 10) -> List[Movie]:
        """Fuzzy search using pg_trgm similarity."""
        sql = text("""
            SELECT id
            FROM movies
            WHERE is_active = true
              AND (
                similarity(COALESCE(title_original, ''), CAST(:q AS TEXT)) > 0.15
                OR similarity(COALESCE(title_uz, ''), CAST(:q AS TEXT)) > 0.15
                OR similarity(COALESCE(title_ru, ''), CAST(:q AS TEXT)) > 0.15
                OR similarity(COALESCE(title_en, ''), CAST(:q AS TEXT)) > 0.15
              )
            ORDER BY GREATEST(
                similarity(COALESCE(title_original, ''), CAST(:q AS TEXT)),
                similarity(COALESCE(title_uz, ''), CAST(:q AS TEXT)),
                similarity(COALESCE(title_ru, ''), CAST(:q AS TEXT)),
                similarity(COALESCE(title_en, ''), CAST(:q AS TEXT))
            ) DESC
            LIMIT :limit
        """)
        result = await self.session.execute(sql, {"q": query, "limit": limit})
        rows = result.fetchall()
        # Convert to Movie-like objects by fetching ids
        if not rows:
            return []
        ids = [row[0] for row in rows]
        movies_result = await self.session.execute(
            select(Movie).where(Movie.id.in_(ids))
        )
        movies = {m.id: m for m in movies_result.scalars().all()}
        return [movies[i] for i in ids if i in movies]

    async def smart_search(self, query: str, limit: int = 10) -> Tuple[List[Movie], str]:
        """
        Returns (movies, search_type)
        search_type: 'code' | 'exact' | 'fuzzy' | 'none'
        """
        query = query.strip()

        # 1. Try code search if digits only
        if query.isdigit():
            movie = await self.search_by_code(query)
            if movie:
                return [movie], "code"

        # 2. Exact ILIKE search
        movies = await self.search_exact(query, limit=limit)
        if movies:
            return movies, "exact"

        # 3. Fuzzy search
        movies = await self.search_fuzzy(query, limit=limit)
        if movies:
            return movies, "fuzzy"

        return [], "none"

    # ─── Stats ────────────────────────────────────────────────────────────────

    async def increment_views(self, movie_id: int):
        movie = await self.get_by_id(movie_id)
        if movie:
            movie.views_count += 1
            await self.session.commit()

    async def increment_version_downloads(self, version_id: int):
        version = await self.get_version(version_id)
        if version:
            version.downloads_count += 1
            await self.session.commit()

    async def increment_episode_version_downloads(self, version_id: int):
        version = await self.get_episode_version(version_id)
        if version:
            version.downloads_count += 1
            await self.session.commit()

    # ─── Saved ────────────────────────────────────────────────────────────────

    async def is_saved(self, user_id: int, movie_id: int) -> bool:
        result = await self.session.execute(
            select(SavedMovie).where(
                SavedMovie.user_id == user_id,
                SavedMovie.movie_id == movie_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def toggle_save(self, user_id: int, movie_id: int) -> bool:
        """Returns True if saved, False if removed."""
        existing = await self.session.execute(
            select(SavedMovie).where(
                SavedMovie.user_id == user_id,
                SavedMovie.movie_id == movie_id,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            await self.session.delete(row)
            await self.session.commit()
            return False
        else:
            self.session.add(SavedMovie(user_id=user_id, movie_id=movie_id))
            await self.session.commit()
            return True

    async def get_saved_movies(self, user_id: int) -> List[Movie]:
        result = await self.session.execute(
            select(Movie)
            .join(SavedMovie, SavedMovie.movie_id == Movie.id)
            .where(SavedMovie.user_id == user_id, Movie.is_active == True)
            .order_by(SavedMovie.created_at.desc())
        )
        return result.scalars().all()

    # ─── Download logging ────────────────────────────────────────────────────

    async def log_download(self, user_id: int, movie_id: int, version_id: Optional[int] = None):
        log = DownloadLog(user_id=user_id, movie_id=movie_id, version_id=version_id)
        self.session.add(log)
        await self.session.commit()

    # ─── Admin: Create / Update ───────────────────────────────────────────────

    async def get_next_movie_code(self) -> str:
        result = await self.session.execute(select(Movie.code))
        codes = result.scalars().all()
        used_codes = {int(c) for c in codes if c.isdigit()}
        code = 10
        while code in used_codes:
            code += 1
        return str(code)

    async def create_movie(self, data: dict) -> Movie:
        movie = Movie(**data)
        self.session.add(movie)
        await self.session.commit()
        await self.session.refresh(movie)
        return movie

    async def update_movie(self, movie_id: int, data: dict) -> Optional[Movie]:
        movie = await self.get_by_id(movie_id)
        if not movie:
            return None
        for k, v in data.items():
            setattr(movie, k, v)
        await self.session.commit()
        return movie

    async def delete_movie(self, movie_id: int):
        movie = await self.get_by_id(movie_id)
        if movie:
            movie.is_active = False
            await self.session.commit()

    async def add_movie_version(self, data: dict) -> MovieVersion:
        version = MovieVersion(**data)
        self.session.add(version)
        await self.session.commit()
        await self.session.refresh(version)
        return version

    async def add_episode(self, movie_id: int, episode_number: int, title: Optional[str] = None) -> Episode:
        episode = Episode(movie_id=movie_id, episode_number=episode_number, title=title)
        self.session.add(episode)
        await self.session.commit()
        await self.session.refresh(episode)
        return episode

    async def add_episode_version(self, data: dict) -> EpisodeVersion:
        version = EpisodeVersion(**data)
        self.session.add(version)
        await self.session.commit()
        await self.session.refresh(version)
        return version

    async def get_all_movies(self, limit: int = 50, offset: int = 0) -> List[Movie]:
        result = await self.session.execute(
            select(Movie)
            .where(Movie.is_active == True)
            .order_by(Movie.created_at.desc())
            .limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def count_movies(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Movie).where(Movie.is_active == True)
        )
        return result.scalar_one()
