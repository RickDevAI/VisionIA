import os
import sqlite3 as _sqlite3
import json
import urllib.request
import urllib.error

TURSO_URL = os.getenv("TURSO_URL", "").rstrip("/")
TURSO_TOKEN = os.getenv("TURSO_TOKEN", "")
DB_PATH = os.getenv("DB_PATH", "usuarios.db")

_USANDO_TURSO = bool(TURSO_URL and TURSO_TOKEN)

if _USANDO_TURSO and TURSO_URL.startswith("libsql://"):
    HTTP_URL = "https://" + TURSO_URL[len("libsql://"):]
else:
    HTTP_URL = TURSO_URL


class Row(dict):
    """
    Emula sqlite3.Row, permitindo acesso por nome da coluna.
    """

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


def _converter_parametro(valor):
    if valor is None:
        return {"type": "null"}

    if isinstance(valor, bool):
        return {"type": "integer", "value": int(valor)}

<<<<<<< HEAD
    def _http_execute(self, sql, params=()):
        """Executa um statement via HTTP e retorna o resultado."""
        stmt = {"type": "execute", "stmt": {"sql": sql}}
        if params:
       stmt["stmt"]["args"] = [
           {"type": "null"} if p is None
           else {"type": "integer", "value": str(int(p))} if isinstance(p, int) and not isinstance(p, bool)
           else {"type": "float",   "value": str(p)} if isinstance(p, float)
           else {"type": "text",    "value": str(p)}
           for p in params
           ]
      
        payload = json.dumps({"requests": [stmt, {"type": "close"}]}).encode()
        req = urllib.request.Request(self._url, data=payload, headers=self._headers, method="POST")
=======
    if isinstance(valor, int):
        return {"type": "integer", "value": valor}

    if isinstance(valor, float):
        return {"type": "float", "value": valor}
>>>>>>> 39717d1 (Corrige db.py para conexão com Turso)

    return {"type": "text", "value": str(valor)}


def _parse_valor(valor):
    if valor is None:
        return None

    if not isinstance(valor, dict):
        return valor

    tipo = valor.get("type")
    val = valor.get("value")

    if tipo == "null":
        return None

<<<<<<< HEAD
    def commit(self):
        pass  

    def close(self):
        pass 
=======
    if tipo == "integer":
        return int(val) if val is not None else None

    if tipo == "float":
        return float(val) if val is not None else None
>>>>>>> 39717d1 (Corrige db.py para conexão com Turso)

    return val


class TursoCursor:
    def __init__(self, resultado):
        cols = [col["name"] for col in resultado.get("cols", [])]
        rows = resultado.get("rows", [])

        self._rows = [
            Row(zip(cols, [_parse_valor(valor) for valor in row]))
            for row in rows
        ]

        self.rowcount = resultado.get("affected_row_count", len(self._rows))
        self.lastrowid = resultado.get("last_insert_rowid")

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows

    def __iter__(self):
        return iter(self._rows)


class TursoDirectCursor:
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


class TursoConnection:
    """
    Conexão com Turso via HTTP REST API.
    Usa apenas bibliotecas padrão do Python.
    """

    def __init__(self):
        self._url = f"{HTTP_URL}/v2/pipeline"
        self._headers = {
            "Authorization": f"Bearer {TURSO_TOKEN}",
            "Content-Type": "application/json",
        }

    def _http_execute(self, sql, params=()):
        stmt = {
            "type": "execute",
            "stmt": {
                "sql": sql
            }
        }

        if params:
            stmt["stmt"]["args"] = [
                _converter_parametro(param)
                for param in params
            ]

        payload = json.dumps({
            "requests": [
                stmt,
                {"type": "close"}
            ]
        }).encode("utf-8")

        req = urllib.request.Request(
            self._url,
            data=payload,
            headers=self._headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            raise RuntimeError(f"Turso HTTP {e.code}: {body}") from e
        except Exception as e:
            raise RuntimeError(f"Erro ao conectar no Turso: {e}") from e

        resultado_pipeline = data["results"][0]

        if resultado_pipeline.get("type") == "error":
            erro = resultado_pipeline.get("error", {})
            mensagem = erro.get("message", "Erro desconhecido no Turso")
            raise RuntimeError(f"Turso error: {mensagem}")

        response = resultado_pipeline.get("response", {})
        result = response.get("result", {})

        return result

    def execute(self, sql, params=()):
        resultado = self._http_execute(sql, params)
        return TursoCursor(resultado)

    def executescript(self, sql):
        comandos = [
            comando.strip()
            for comando in sql.split(";")
            if comando.strip()
        ]

        for comando in comandos:
            self._http_execute(comando)

        return self

    def cursor(self):
        return TursoDirectCursor(self)

    def commit(self):
        pass

    def close(self):
        pass

    @property
    def total_changes(self):
        return 1


def conectar():
    """
    Retorna conexão com o banco.
    - Local: SQLite
    - Produção: Turso, se TURSO_URL e TURSO_TOKEN existirem
    """

    if _USANDO_TURSO:
        return TursoConnection()

    conn = _sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = _sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def usando_turso() -> bool:
    return _USANDO_TURSO