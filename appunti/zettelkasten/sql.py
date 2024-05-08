"""
SQLite statements to manage index
"""

import sqlite3
from pathlib import Path

from typing import Optional

from appunti.zettelkasten.notes import Note

_CREATE_MAIN_TABLE_STMT = """
    CREATE TABLE IF NOT EXISTS zettelkasten(zk_id STRING NOT NULL,
    title STRING NOT NULL,
    author STRING NOT NULL,
    creation_date DATETIME NOT NULL,
    last_changed DATETIME NOT NULL,
    PRIMARY KEY(zk_id))
"""
_CREATE_TAGS_TABLE_STMT = """
    CREATE TABLE IF NOT EXISTS tags(tag STRING NOT NULL,
    zk_id STRING NOT NULL,
    PRIMARY KEY(zk_id, tag),
    FOREIGN KEY(zk_id) REFERENCES zettelkasten(zk_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE)
"""
_CREATE_LINKS_TABLE_STMT = """
    CREATE TABLE IF NOT EXISTS links(link STRING NOT NULL,
    zk_id STRING NOT NULL,
    PRIMARY KEY(zk_id, link),
    FOREIGN KEY(zk_id) REFERENCES zettelkasten(zk_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE)
"""
_DROP_MAIN_TABLE_STMT = "DROP TABLE IF EXISTS zettelkasten;"
_DROP_TAGS_TABLE_STMT = "DROP TABLE IF EXISTS tags;"
_DROP_LINKS_TABLE_STMT = "DROP TABLE IF EXISTS links;"
_INSERT_MAIN_STMT = "INSERT INTO zettelkasten VALUES (?, ?, ?, ?, ?)"
_INSERT_TAGS_STMT = "INSERT INTO tags VALUES (?, ?)"
_INSERT_LINKS_STMT = "INSERT INTO links VALUES (?, ?)"
_DELETE_MAIN_STMT = "DELETE FROM zettelkasten WHERE zk_id = ?"
_DELETE_TAGS_STMT = "DELETE FROM tags WHERE zk_id = ?"
_DELETE_LINKS_STMT = "DELETE FROM links WHERE zk_id = ?"
_UPDATE_MAIN_STMT = """
    UPDATE zettelkasten SET
    title = ?,
    author = ?,
    last_changed = ?
    WHERE zk_id = ?
"""
_LIST_STMT = "SELECT zk_id, title FROM zettelkasten;"
_GET_LINKS_ID = "SELECT link FROM links WHERE zk_id = ?;"

_JOINED_ALL = """
    (SELECT *
    FROM (
            SELECT * FROM zettelkasten
            LEFT JOIN tags ON zettelkasten.zk_id = tags.zk_id
        ) tmp
        LEFT JOIN links ON tmp.zk_id = links.zk_id)
"""


class DBManager:
    """
    Database manager for the index of a zettelkasten.

    :param connection: the connection to the index
    """

    def __init__(self, index: Path) -> None:
        self.index = index

    def create_tables(self) -> None:
        """
        Create the index for a newly initialized zk.
        """
        with sqlite3.connect(self.index) as conn:
            conn.execute(_CREATE_MAIN_TABLE_STMT)
            conn.execute(_CREATE_TAGS_TABLE_STMT)
            conn.execute(_CREATE_LINKS_TABLE_STMT)

    def drop_tables(self) -> None:
        """
        Drop all the tables.
        """
        with sqlite3.connect(self.index) as conn:
            conn.execute(_DROP_MAIN_TABLE_STMT)
            conn.execute(_DROP_TAGS_TABLE_STMT)
            conn.execute(_DROP_LINKS_TABLE_STMT)

    def update_note_to_index(self, note: Note) -> None:
        """
        Add to the index the updated metadata of the note.

        :param note: the updated note.
        """
        main_payload = (note.title, note.author, note.last, note.zk_id)
        tags_payload = [(tag, note.zk_id) for tag in note.tags]
        links_payload = [(link, note.zk_id) for link in note.links]

        try:
            with sqlite3.connect(self.index) as conn:
                conn.execute(_UPDATE_MAIN_STMT, main_payload)
                # update tags and links
                conn.execute(_DELETE_TAGS_STMT, (note.zk_id, ))
                conn.execute(_DELETE_LINKS_STMT, (note.zk_id, ))
                conn.executemany(_INSERT_TAGS_STMT, tags_payload)
                conn.executemany(_INSERT_LINKS_STMT, links_payload)
        # TODO: investigate sqlite3 exceptions
        except sqlite3.IntegrityError as e:
            raise DBManagerException("SQL error") from e

    # TODO: make it so payload is note-agnostic
    def add_to_index(self, note: Note) -> None:
        """
        Add a new note to the vault

        :param note: note to process.
        """
        main_payload = (note.zk_id, note.title, note.author, note.date,
                        note.last)
        tags_payload = [(tag, note.zk_id) for tag in note.tags]
        links_payload = [(link, note.zk_id) for link in note.links]

        try:
            with sqlite3.connect(self.index) as conn:
                conn.execute(_INSERT_MAIN_STMT, main_payload)
                conn.executemany(_INSERT_TAGS_STMT, tags_payload)
                conn.executemany(_INSERT_LINKS_STMT, links_payload)
        except sqlite3.IntegrityError as e:
            raise DBManagerException("SQL error") from e

    def delete_from_index(self, zk_id: str) -> None:
        """
        Delete note from index.

        :param note: note to delete.
        """
        try:
            with sqlite3.connect(self.index) as conn:
                conn.execute(_DELETE_MAIN_STMT, (zk_id, ))
        except sqlite3.IntegrityError as e:
            raise DBManagerException("SQL error") from e

    # TODO: needs improvements in performance. Maybe don't build
    # a huge join but build incrementally?
    def list_notes(
            self,
            title: Optional[list[str]] = None,
            zk_id: Optional[list[str]] = None,
            author: Optional[list[str]] = None,
            tag: Optional[list[str]] = None,
            link: Optional[list[str]] = None,
            # creation_date: Optional[list[str]] = None,
            # access_date: Optional[list[str]] = None,
            sort_by: Optional[str] = None,
            descending: bool = True,
            show: list[str] = ['title', 'zk_id']) -> list[tuple[str, ...]]:
        """
        """
        query: str = _JOINED_ALL
        payload = []
        select_cols = "SELECT DISTINCT " + ", ".join(
            f"{col}" for col in show) + " FROM "

        queries = []
        for name, table in [('title', 'zettelkasten'),
                            ('zk_id', 'zettelkasten'),
                            ('author', 'zettelkasten'), ('tag', 'tags'),
                            ('link', 'links')]:

            value = locals()[name]
            if value is None:
                continue
            tmp_query, tmp_payload = self._assemble_templated_query(
                table, name, value)
            payload += tmp_payload
            queries.append(tmp_query)

        sub_queries = " AND ".join(
            [f"zk_id IN ({tmp_query})" for tmp_query in queries])
        where_query = " WHERE " + sub_queries if sub_queries else ""

        ascending_query = "DESC" if descending else "ASC"
        sort_query = ""
        if sort_by is not None:
            sort_query = f"\nORDER BY {sort_by} {ascending_query}"

        query = select_cols + query + where_query + sort_query

        try:
            with sqlite3.connect(self.index) as conn:
                cur = conn.cursor()
                results = cur.execute(query, tuple(payload)).fetchall()
                cur.close()
        except sqlite3.OperationalError as e:
            raise DBManagerException(
                "Something went wrong. Have you tried indexing your notes first?"
                f"\nError: {e}")

        return results
        # return query

    @staticmethod
    def _assemble_templated_query(
            table_name: str, column_name: str,
            column_values: list[str]) -> tuple[str, list[str]]:
        query_template = "SELECT zk_id FROM {} WHERE zk_id IN ({})"
        query = f"SELECT zk_id from {table_name}"
        payload: list[str] = []
        for element in column_values:
            query = query_template.format(table_name, query)
            if element.startswith("!"):
                query += f" AND zk_id NOT IN (SELECT zk_id FROM {table_name} WHERE {column_name} LIKE ?)"
                payload.append(element.removeprefix("!"))
            else:
                query += f" AND {column_name} LIKE ?"
                payload.append(element)

        return query, payload

    def get_title(self) -> list[str]:
        with sqlite3.connect(self.index) as conn:
            results = conn.execute("select title from zettelkasten").fetchall()

        return results

    def get_zk_id(self, ) -> list[str]:
        """
        """
        with sqlite3.connect(self.index) as conn:
            results = conn.execute("select zk_id from zettelkasten").fetchall()

        return results


class DBManagerException(Exception):
    """Errors related to the index database"""
