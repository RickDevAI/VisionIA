import os
import sqlite3 as _sqlite3

TURSO_URL   = os.getenv("TURSO_URL", "")
TURSO_TOKEN = os.getenv("TURSO_TOKEN", "")
DB_PATH     = os.getenv("DB_PATH", "usuarios.db")

_USANDO_TURSO = bool(TURSO_URL and TURSO_TOKEN)

if _USANDO_TURSO:
    import libsql_client


# Esta classe emula sqlite3.Row para que o código de api.py não mude.

class Row(dict):
    """Dict com acesso por atributo, emula sqlite3.Row."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class TursoConnection:
    """
    Wrapper síncrono sobre o libsql-client assíncrono.
    Expõe a mesma interface que sqlite3.Connection:
      conn.execute(sql, params) → TursoCursor
      conn.executescript(sql)
      conn.commit()  (no-op — Turso auto-commita)
      conn.close()
    """

    def __init__(self, client):
        self._client = client
        import asyncio
        self._loop = asyncio.new_event_loop()

    def _run(self, coro):
        return self._loop.run_until_complete(coro)

    def execute(self, sql, params=()):
        rs = self._run(self._client.execute(sql, list(params)))
        return TursoCursor(rs)

    def executescript(self, sql):
        stmts = [s.strip() for s in sql.split(";") if s.strip()]
        for stmt in stmts:
            self._run(self._client.execute(stmt))
        return self

    def cursor(self):
        return TursoDirectCursor(self)

    def commit(self):
        pass 

    def close(self):
        self._run(self._client.close())
        self._loop.close()

    @property
    def total_changes(self):
        return 1  


class TursoCursor:
    """Emula sqlite3.Cursor após um execute()."""

    def __init__(self, result_set):
        cols = [c.name for c in result_set.columns] if result_set.columns else []
        self._rows = [Row(zip(cols, row)) for row in result_set.rows]
        self.rowcount = result_set.rows_affected if hasattr(result_set, "rows_affected") else len(self._rows)
        self.lastrowid = result_set.last_insert_rowid if hasattr(result_set, "last_insert_rowid") else None

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows

    def __iter__(self):
        return iter(self._rows)


class TursoDirectCursor:
    """Cursor obtido via conn.cursor() — delega para conn.execute()."""

    def __init__(self, conn):
        self._conn = conn
        self._cursor = None

    def execute(self, sql, params=()):
        self._cursor = self._conn.execute(sql, params)
        return self._cursor

    def executescript(self, sql):
        return self._conn.executescript(sql)

    def fetchone(self):
        return self._cursor.fetchone() if self._cursor else None

    def fetchall(self):
        return self._cursor.fetchall() if self._cursor else []

    @property
    def rowcount(self):
        return self._cursor.rowcount if self._cursor else 0


# ─── API pública ────────

def conectar():
    """
    Retorna uma conexão com o banco.
    Transparente: sqlite3 localmente, Turso em produção.
    """
    if _USANDO_TURSO:
        client = libsql_client.create_client_sync(
            url=TURSO_URL,
            auth_token=TURSO_TOKEN,
        )
        return TursoConnection(client)

    conn = _sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = _sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def usando_turso() -> bool:
    return _USANDO_TURSO
