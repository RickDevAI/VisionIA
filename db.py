"""
db.py — camada de abstração de banco de dados.
 
- Sem TURSO_URL: SQLite local (desenvolvimento)
- Com TURSO_URL + TURSO_TOKEN: Turso via HTTP REST (produção)
  Usa a API HTTP do Turso em vez de WebSocket — mais estável em produção.
"""
 
import os
import sqlite3 as _sqlite3
import json
import urllib.request
import urllib.error
 
TURSO_URL   = os.getenv("TURSO_URL", "").rstrip("/")
TURSO_TOKEN = os.getenv("TURSO_TOKEN", "")
DB_PATH     = os.getenv("DB_PATH", "usuarios.db")
 
_USANDO_TURSO = bool(TURSO_URL and TURSO_TOKEN)
 
# Converte URL libsql:// para https://
if _USANDO_TURSO and TURSO_URL.startswith("libsql://"):
    _HTTP_URL = "https://" + TURSO_URL[len("libsql://"):]
else:
    _HTTP_URL = TURSO_URL
 
 
class Row(dict):
    """Dict com acesso por índice, emula sqlite3.Row."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)
 
 
class TursoConnection:
    """Conexão com Turso via HTTP REST API."""
 
    def __init__(self):
        self._url = f"{_HTTP_URL}/v2/pipeline"
        self._headers = {
            "Authorization": f"Bearer {TURSO_TOKEN}",
            "Content-Type": "application/json",
        }
 
    def _http_execute(self, sql, params=()):
        """Executa um statement via HTTP e retorna o resultado."""
        stmt = {"type": "execute", "stmt": {"sql": sql}}
        if params:
            stmt["stmt"]["args"] = [
                {"type": "text", "value": str(p)} if isinstance(p, str)
                else {"type": "integer", "value": p} if isinstance(p, int)
                else {"type": "float", "value": p} if isinstance(p, float)
                else {"type": "null"} if p is None
                else {"type": "text", "value": str(p)}
                for p in params
            ]
 
        payload = json.dumps({"requests": [stmt, {"type": "close"}]}).encode()
        req = urllib.request.Request(self._url, data=payload, headers=self._headers, method="POST")
 
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"Turso HTTP {e.code}: {body}")
 
        result = data["results"][0]
        if result["type"] == "error":
            raise RuntimeError(f"Turso error: {result['error']['message']}")
 
        return result["response"]["result"]
 
    def execute(self, sql, params=()):
        result = self._http_execute(sql, params)
        return TursoCursor(result)
 
    def executescript(self, sql):
        stmts = [s.strip() for s in sql.split(";") if s.strip()]
        for stmt in stmts:
            self._http_execute(stmt)
        return self
 
    def cursor(self):
        return TursoDirectCursor(self)
 
    def commit(self):
        pass  # Turso auto-commita
 
    def close(self):
        pass  # HTTP é stateless, nada a fechar
 
    @property
    def total_changes(self):
        return 1
 
 
class TursoCursor:
    def __init__(self, result):
        cols = [c["name"] for c in result.get("cols", [])]
        self._rows = [
            Row(zip(cols, [_parse_val(v) for v in row]))
            for row in result.get("rows", [])
        ]
        self.rowcount  = result.get("affected_row_count", len(self._rows))
        self.lastrowid = result.get("last_insert_rowid")
 
    def fetchone(self):
        return self._rows[0] if self._rows else None
 
    def fetchall(self):
        return self._rows
 
    def __iter__(self):
        return iter(self._rows)
 
 
class TursoDirectCursor:
    def __init__(self, conn):
        self._conn   = conn
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
 
 
def _parse_val(v):
    """Converte valor do formato Turso para Python."""
    if v is None or (isinstance(v, dict) and v.get("type") == "null"):
        return None
    if isinstance(v, dict):
        t = v.get("type", "text")
        val = v.get("value")
        if t == "integer": return int(val) if val is not None else None
        if t == "float":   return float(val) if val is not None else None
        return val
    return v
 
 
def conectar():
    """Retorna conexão com o banco."""
    if _USANDO_TURSO:
        return TursoConnection()
 
    conn = _sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = _sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn
 
 
def usando_turso() -> bool:
    return _USANDO_TURSO