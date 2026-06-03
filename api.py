from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, List
from collections import defaultdict
import time

import numpy as np
from PIL import Image, UnidentifiedImageError
from ultralytics import YOLO
from pydantic import BaseModel, EmailStr
from db import conectar, usando_turso
import io
import os
import re

# =========================
# API
# =========================
app = FastAPI(
    title="GMS Screenshot Validator",
    description="Validação de telas do fluxo GMS Android usando YOLOv8",
    version="2.0.0"
)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    import secrets
    SECRET_KEY = secrets.token_hex(32)
    print("AVISO: SECRET_KEY não definida. Gerando chave temporária — tokens não sobreviverão a reinicializações!")

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 2

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# RATE LIMITING
# =========================
_rate_store: dict[str, list[float]] = defaultdict(list)

RATE_LIMIT_REQUESTS = 20  
RATE_LIMIT_WINDOW   = 60  

def checar_rate_limit(identificador: str):
    agora = time.time()
    janela = _rate_store[identificador]
    # Remove timestamps fora da janela
    _rate_store[identificador] = [t for t in janela if agora - t < RATE_LIMIT_WINDOW]
    if len(_rate_store[identificador]) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Muitas requisições. Aguarde alguns segundos e tente novamente."
        )
    _rate_store[identificador].append(agora)


# =========================
# MODELO DA IA
# =========================
def encontrar_melhor_modelo(base_dir: str = "runs/classify") -> str:
    """
    Varre todos os runs e retorna o caminho do best.pt
    com a maior accuracy_top1 no último epoch.
    """
    melhor_path = None
    melhor_acc   = -1.0

    if not os.path.isdir(base_dir):
        return os.getenv("CLASSIFIER_PATH", "runs/classify/visionia_cls/weights/best.pt")

    for run in os.listdir(base_dir):
        results_csv = os.path.join(base_dir, run, "results.csv")
        best_pt     = os.path.join(base_dir, run, "weights", "best.pt")

        if not os.path.exists(results_csv) or not os.path.exists(best_pt):
            continue

        try:
            with open(results_csv) as f:
                linhas = f.read().strip().splitlines()
            if len(linhas) < 2:
                continue
            headers = [h.strip() for h in linhas[0].split(",")]
            valores = [v.strip() for v in linhas[-1].split(",")]
            row = dict(zip(headers, valores))
            acc = float(row.get("metrics/accuracy_top1", 0))
            if acc > melhor_acc:
                melhor_acc  = acc
                melhor_path = best_pt
        except Exception:
            continue

    if melhor_path:
        print(f"Melhor modelo encontrado: {melhor_path} (accuracy_top1={melhor_acc:.4f})")
        return melhor_path

    fallback = os.getenv("CLASSIFIER_PATH", "runs/classify/visionia_cls/weights/best.pt")
    print(f"Nenhum run válido encontrado. Usando fallback: {fallback}")
    return fallback


CLASSIFIER_PATH = encontrar_melhor_modelo()

if os.path.exists(CLASSIFIER_PATH):
    cls_model = YOLO(CLASSIFIER_PATH)
    print(f"Modelo carregado: {CLASSIFIER_PATH}")
else:
    cls_model = None
    print(f"AVISO: modelo não encontrado em: {CLASSIFIER_PATH}")


# =========================


def criar_tabelas():
    conn = conectar()
    try:
        cur = conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            nome               TEXT,
            email              TEXT UNIQUE NOT NULL,
            senha              TEXT NOT NULL,
            telefone           TEXT,
            receber_relatorios INTEGER DEFAULT 0,
            role               TEXT DEFAULT 'QA Analyst',
            criado_em          TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS analises (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_email  TEXT NOT NULL,
            nome_arquivo   TEXT NOT NULL,
            status         TEXT NOT NULL,
            score          REAL NOT NULL,
            tipo_tela      TEXT,
            detectados     TEXT,
            problemas      TEXT,
            classe_predita TEXT,
            top5_classes   TEXT,
            tempo_ms       REAL,
            data_analise   TEXT NOT NULL
        );
        """)

        for col, definition in [
            ("criado_em",    "TEXT DEFAULT (datetime('now'))"),
            ("classe_predita","TEXT"),
            ("top5_classes", "TEXT"),
            ("tempo_ms",     "REAL"),
        ]:
            try:
                cur.execute(f"ALTER TABLE analises ADD COLUMN {col} {definition}")
            except Exception:
                pass  
        try:
            cur.execute("ALTER TABLE usuarios ADD COLUMN criado_em TEXT DEFAULT (datetime('now'))")
        except Exception:
            pass

        conn.commit()
    finally:
        conn.close()

criar_tabelas()


# =========================
# MODELS
# =========================
class UserRegister(BaseModel):
    nome: Optional[str] = None
    email: EmailStr
    senha: str
    telefone: Optional[str] = None

class UserAuth(BaseModel):
    email: EmailStr
    senha: str

class UserSettingsUpdate(BaseModel):
    nome: Optional[str] = None
    email: EmailStr
    telefone: Optional[str] = None
    receber_relatorios: Optional[bool] = False


# =========================
# AUTH
# =========================
def senha_forte(senha: str) -> bool:
    return (
        len(senha) >= 8
        and re.search(r"[A-Z]", senha)
        and re.search(r"[a-z]", senha)
        and re.search(r"\d", senha)
        and re.search(r"[^A-Za-z0-9]", senha)
    )

def criar_token(email: str) -> str:
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verificar_token(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não enviado")
    partes = authorization.split()
    if len(partes) != 2 or partes[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Formato do token inválido")
    try:
        payload = jwt.decode(partes[1], SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


# =========================
# CLASSIFICAÇÃO IA
# =========================
CLASSES_VALIDAS = {
    "valida", "valid", "oficial",
    "home_valida", "browser_valida", "feed_valida", "gemini_valida"
}
CLASSES_INVALIDAS = {
    "invalida", "invalid", "fake",
    "home_invalida", "browser_invalida", "feed_invalida", "gemini_invalida",
    "assist_invalida", "geral_invalida",
}

# =========================
# PASS_THRESHOLD  : confiança mínima para aprovar uma screenshot válida   (padrão 75%)
# WARN_THRESHOLD  : confiança mínima para emitir WARNING em vez de FAIL   (padrão 50%)
# CONF_THRESHOLD  : confiança mínima para o modelo inferir qualquer classe (padrão 40%)
# =========================
PASS_THRESHOLD = float(os.getenv("PASS_THRESHOLD", "75"))
WARN_THRESHOLD = float(os.getenv("WARN_THRESHOLD", "50"))
CONF_THRESHOLD = float(os.getenv("CONF_THRESHOLD", "40"))

def mapear_resultado_classe(classe_nome: str, confianca: float):
    nome = classe_nome.strip().lower()
    is_valida = nome in CLASSES_VALIDAS or bool(re.search(r"(^|_)valida$", nome)) or nome in ["valid", "oficial"]
    is_invalida = nome in CLASSES_INVALIDAS or any(x in nome for x in ["invalida", "invalid", "fake"])

    if is_valida:
        if confianca >= PASS_THRESHOLD:
            return "PASS", []
        if confianca >= WARN_THRESHOLD:
            return "WARNING", [f"Confiança abaixo do limiar de aprovação ({PASS_THRESHOLD:.0f}%)"]
        return "WARNING", ["Baixa confiança para aprovação automática"]

    if is_invalida:
        if confianca >= WARN_THRESHOLD:
            return "FAIL", ["Screenshot fora do padrão oficial aprendido pela IA"]
        return "WARNING", ["Baixa confiança para reprovação automática — verifique manualmente"]

    return "WARNING", ["Classe prevista não mapeada com confiança suficiente"]

def inferir_tipo_tela(classe_nome: str) -> str:
    nome = classe_nome.lower()
    if "home"    in nome: return "HOME"
    if "browser" in nome: return "BROWSER"
    if "feed"    in nome: return "GOOGLE_FEED"
    if "gemini"  in nome: return "GEMINI_LOGIN"
    return "CLASSIFICACAO_VISUAL"

TIPO_TELA_LABELS = {
    "HOME": "Tela inicial",
    "BROWSER": "Navegador",
    "GOOGLE_FEED": "Google Feed",
    "GEMINI_LOGIN": "Login do Gemini",
    "CLASSIFICACAO_VISUAL": "Classificação visual",
    "UNKNOWN": "Desconhecida",
}

def formatar_tipo_tela(tipo: str) -> str:
    return TIPO_TELA_LABELS.get(tipo, tipo)

def gerar_comentario(status: str, tipo_tela: str, problemas: list, detectados: list) -> str:
    label = formatar_tipo_tela(tipo_tela).lower()
    if status == "PASS":
        if detectados:
            return f"A IA considerou a screenshot válida porque encontrou {', '.join(detectados)} dentro do padrão esperado para {label}."
        return f"A IA considerou a screenshot válida porque ela está dentro do padrão visual esperado para {label}."
    if status == "WARNING":
        if problemas:
            return f"A IA sinalizou a screenshot para revisão porque encontrou possíveis inconsistências em {label}."
        return f"A IA sinalizou a screenshot para revisão por baixa confiança na análise de {label}."
    if problemas:
        return f"A IA considerou a screenshot inválida porque identificou inconsistências no padrão esperado para {label}."
    return f"A IA considerou a screenshot inválida porque ela está fora do padrão visual esperado para {label}."


def analisar_screenshot(frame: np.ndarray) -> dict:
    if cls_model is None:
        raise RuntimeError(f"Modelo não carregado. Verifique: {CLASSIFIER_PATH}")

    inicio = time.perf_counter()
    resultado = cls_model(frame, verbose=False)[0]
    tempo_ms = (time.perf_counter() - inicio) * 1000

    probs = resultado.probs
    classe_idx  = int(probs.top1)
    confianca   = float(probs.top1conf) * 100
    classe_nome = resultado.names[classe_idx]

    top5_idx    = probs.top5
    top5_conf   = probs.top5conf.tolist()
    top5 = [
        {"classe": resultado.names[int(i)], "confianca": round(float(c) * 100, 2)}
        for i, c in zip(top5_idx, top5_conf)
    ]

    status, problemas = mapear_resultado_classe(classe_nome, confianca)
    tipo_tela         = inferir_tipo_tela(classe_nome)
    tipo_tela_label   = formatar_tipo_tela(tipo_tela)
    detectados        = [f"padrão visual compatível com {tipo_tela_label.lower()}"] if status == "PASS" else []
    comentario        = gerar_comentario(status, tipo_tela, problemas, detectados)

    resumo_map = {
        "PASS":    f"Screenshot reconhecida como válida pela IA ({classe_nome}).",
        "WARNING": f"Screenshot classificada com alerta pela IA ({classe_nome}).",
        "FAIL":    f"Screenshot reconhecida como não válida pela IA ({classe_nome}).",
    }

    return {
        "status":              status,
        "score":               round(confianca, 2),
        "tipo_tela":           tipo_tela,
        "tipo_tela_label":     tipo_tela_label,
        "detectados":          detectados,
        "problemas":           problemas,
        "resumo":              resumo_map.get(status, ""),
        "comentario_validacao": comentario,
        "classe_predita":      classe_nome,
        "top5_classes":        top5,
        "tempo_ms":            round(tempo_ms, 2),
    }


# =========================
# HELPERS
# =========================
def ler_e_validar_imagem(contents: bytes) -> np.ndarray:
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande (máx. 10 MB)")
    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Arquivo não é uma imagem válida")
    if image.width < 300 or image.height < 300:
        raise HTTPException(status_code=400, detail="Imagem muito pequena (mín. 300x300 px)")
    return np.array(image)


def salvar_analise(email: str, nome_arquivo: str, resultado: dict):
    conn = conectar()
    try:
        conn.execute("""
            INSERT INTO analises (
                usuario_email, nome_arquivo, status, score, tipo_tela,
                detectados, problemas, classe_predita, top5_classes, tempo_ms, data_analise
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email,
            nome_arquivo,
            resultado["status"],
            float(resultado["score"]),
            resultado["tipo_tela"],
            ", ".join(resultado.get("detectados", [])),
            " | ".join(resultado.get("problemas", [])),
            resultado.get("classe_predita", ""),
            str(resultado.get("top5_classes", [])),
            resultado.get("tempo_ms"),
            datetime.utcnow().isoformat(),
        ))
        conn.commit()
    finally:
        conn.close()


# =========================
# ROTAS — Auth
# =========================
@app.get("/", tags=["status"])
def root():
    return {
        "status": "online",
        "version": "2.0.0",
        "model_loaded": cls_model is not None,
        "model_path": CLASSIFIER_PATH,
        "thresholds": {
            "pass":  PASS_THRESHOLD,
            "warn":  WARN_THRESHOLD,
            "conf":  CONF_THRESHOLD,
        },
    }


@app.post("/register", tags=["auth"])
async def register(data: UserRegister):
    if not senha_forte(data.senha):
        raise HTTPException(
            status_code=400,
            detail="A senha deve ter no mínimo 8 caracteres, com letra maiúscula, minúscula, número e caractere especial."
        )
    conn = conectar()
    try:
        conn.execute(
            "INSERT INTO usuarios (nome, email, senha, telefone) VALUES (?, ?, ?, ?)",
            (data.nome, data.email.lower(), pwd_context.hash(data.senha), data.telefone)
        )
        conn.commit()
        return {"msg": "Usuário criado com sucesso"}
    except Exception as _e:
        if "UNIQUE" not in str(_e) and "unique" not in str(_e): raise
        raise HTTPException(status_code=400, detail="Email já existe")
    finally:
        conn.close()


@app.post("/login", tags=["auth"])
async def login(data: UserAuth, request: Request):
    checar_rate_limit(f"login:{request.client.host}")
    conn = conectar()
    try:
        row = conn.execute(
            "SELECT nome, email, senha, role FROM usuarios WHERE email = ?",
            (data.email.lower(),)
        ).fetchone()

        if row and pwd_context.verify(data.senha, row["senha"]):
            conn.execute(
                "UPDATE usuarios SET ultimo_login = datetime('now') WHERE email = ?",
                (data.email.lower(),)
            )
            conn.commit()
    finally:
        conn.close()

    if row and pwd_context.verify(data.senha, row["senha"]):
        return {
            "token": criar_token(row["email"]),
            "role":  row["role"],
            "nome":  row["nome"] or "",
            "email": row["email"],
        }
    raise HTTPException(status_code=401, detail="Credenciais inválidas")


# =========================
# ROTAS — Usuário
# =========================
@app.get("/me", tags=["usuario"])
async def me(authorization: str = Header(None)):
    email = verificar_token(authorization)
    conn = conectar()
    try:
        row = conn.execute(
            "SELECT nome, email, telefone, receber_relatorios, role FROM usuarios WHERE email = ?",
            (email,)
        ).fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {
        "nome": row["nome"] or "",
        "email": row["email"],
        "telefone": row["telefone"] or "",
        "receber_relatorios": bool(row["receber_relatorios"]),
        "role": row["role"],
    }


@app.put("/me", tags=["usuario"])
async def atualizar_me(data: UserSettingsUpdate, authorization: str = Header(None)):
    email_token = verificar_token(authorization)
    novo_email = data.email.lower()
    conn = conectar()
    try:
        cur = conn.execute("""
            UPDATE usuarios
            SET nome = ?, email = ?, telefone = ?, receber_relatorios = ?
            WHERE email = ?
        """, (data.nome, novo_email, data.telefone, 1 if data.receber_relatorios else 0, email_token))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
    except Exception as _e:
        if "UNIQUE" not in str(_e) and "unique" not in str(_e): raise
        raise HTTPException(status_code=400, detail="Email já está em uso")
    finally:
        conn.close()

    resposta = {"msg": "Configurações salvas com sucesso"}
    if novo_email != email_token:
        resposta["token"] = criar_token(novo_email)
    return resposta


# =========================
# ROTAS — Validação
# =========================
@app.post("/validar", tags=["validacao"])
async def validar(
    request: Request,
    file: UploadFile = File(...),
    authorization: str = Header(None)
):
    email = verificar_token(authorization)
    checar_rate_limit(f"validar:{email}")

    if file.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Formato não suportado. Use PNG ou JPG.")

    try:
        contents = await file.read()
        frame    = ler_e_validar_imagem(contents)
        resultado = analisar_screenshot(frame)
        salvar_analise(email, file.filename, resultado)
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        print("ERRO /validar:", repr(e))
        raise HTTPException(status_code=500, detail="Erro interno ao analisar a imagem")


@app.post("/validar/lote", tags=["validacao"])
async def validar_lote(
    request: Request,
    files: List[UploadFile] = File(...),
    authorization: str = Header(None)
):
    """Valida múltiplas screenshots em uma única requisição (máx. 20 arquivos)."""
    email = verificar_token(authorization)
    checar_rate_limit(f"validar:{email}")

    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Máximo de 20 arquivos por lote.")

    resultados = []
    for file in files:
        if file.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
            resultados.append({
                "arquivo": file.filename,
                "erro": "Formato não suportado",
                "status": "FAIL",
            })
            continue
        try:
            contents = await file.read()
            frame    = ler_e_validar_imagem(contents)
            res      = analisar_screenshot(frame)
            salvar_analise(email, file.filename, res)
            resultados.append({"arquivo": file.filename, **res})
        except HTTPException as e:
            resultados.append({"arquivo": file.filename, "erro": e.detail, "status": "FAIL"})
        except Exception as e:
            print(f"ERRO /validar/lote [{file.filename}]:", repr(e))
            resultados.append({"arquivo": file.filename, "erro": "Erro interno", "status": "FAIL"})

    aprovadas = sum(1 for r in resultados if r.get("status") == "PASS")
    alertas   = sum(1 for r in resultados if r.get("status") == "WARNING")
    falhas    = sum(1 for r in resultados if r.get("status") == "FAIL")

    return {
        "total": len(resultados),
        "aprovadas": aprovadas,
        "alertas": alertas,
        "falhas": falhas,
        "resultados": resultados,
    }


# =========================
# ROTAS — Histórico e Stats
# =========================
@app.get("/historico", tags=["historico"])
async def historico(authorization: str = Header(None), limite: int = 50, offset: int = 0):
    email = verificar_token(authorization)
    limite = min(max(limite, 1), 200)

    conn = conectar()
    try:
        rows = conn.execute("""
            SELECT nome_arquivo, status, score, tipo_tela, problemas,
                   classe_predita, tempo_ms, data_analise
            FROM analises
            WHERE usuario_email = ?
            ORDER BY data_analise DESC
            LIMIT ? OFFSET ?
        """, (email, limite, offset)).fetchall()
    finally:
        conn.close()

    return [
        {
            "nome_arquivo":   row["nome_arquivo"],
            "status":         row["status"],
            "score":          row["score"],
            "tipo_tela":      row["tipo_tela"],
            "tipo_tela_label": formatar_tipo_tela(row["tipo_tela"] or "UNKNOWN"),
            "problemas":      row["problemas"],
            "classe_predita": row["classe_predita"],
            "tempo_ms":       row["tempo_ms"],
            "data_analise":   row["data_analise"],
        }
        for row in rows
    ]


@app.get("/stats", tags=["historico"])
async def stats(authorization: str = Header(None)):
    """Estatísticas de uso do usuário autenticado."""
    email = verificar_token(authorization)
    conn = conectar()
    try:
        row = conn.execute("""
            SELECT
                COUNT(*)                                         AS total,
                SUM(status = 'PASS')                            AS aprovadas,
                SUM(status = 'WARNING')                         AS alertas,
                SUM(status = 'FAIL')                            AS falhas,
                ROUND(AVG(score), 2)                            AS score_medio,
                ROUND(AVG(tempo_ms), 2)                         AS tempo_medio_ms,
                MIN(data_analise)                               AS primeira_analise,
                MAX(data_analise)                               AS ultima_analise
            FROM analises
            WHERE usuario_email = ?
        """, (email,)).fetchone()

        telas = conn.execute("""
            SELECT tipo_tela, COUNT(*) AS qtd
            FROM analises
            WHERE usuario_email = ?
            GROUP BY tipo_tela
            ORDER BY qtd DESC
        """, (email,)).fetchall()

        # Evolução dos últimos 7 dias
        evolucao = conn.execute("""
            SELECT DATE(data_analise) AS dia,
                   COUNT(*) AS total,
                   SUM(status = 'PASS') AS aprovadas,
                   SUM(status = 'FAIL') AS falhas
            FROM analises
            WHERE usuario_email = ?
              AND data_analise >= datetime('now', '-7 days')
            GROUP BY dia
            ORDER BY dia
        """, (email,)).fetchall()

    finally:
        conn.close()

    total = row["total"] or 0
    return {
        "total":           total,
        "aprovadas":       row["aprovadas"] or 0,
        "alertas":         row["alertas"]   or 0,
        "falhas":          row["falhas"]    or 0,
        "taxa_aprovacao":  round((row["aprovadas"] or 0) / total * 100, 1) if total else 0,
        "score_medio":     row["score_medio"],
        "tempo_medio_ms":  row["tempo_medio_ms"],
        "primeira_analise": row["primeira_analise"],
        "ultima_analise":  row["ultima_analise"],
        "por_tipo_tela": [
            {"tipo_tela": t["tipo_tela"], "label": formatar_tipo_tela(t["tipo_tela"] or "UNKNOWN"), "qtd": t["qtd"]}
            for t in telas
        ],
        "evolucao_7dias": [
            {"dia": e["dia"], "total": e["total"], "aprovadas": e["aprovadas"], "falhas": e["falhas"]}
            for e in evolucao
        ],
    }

# =========================
# ROLE-BASED ACCESS — Admin
# =========================
ROLES_VALIDAS = {"QA Analyst", "QA Lead", "admin"}

def verificar_admin(authorization: Optional[str] = Header(None)) -> str:
    """Verifica token e garante que o usuário tem role 'admin'."""
    email = verificar_token(authorization)
    conn = conectar()
    try:
        row = conn.execute(
            "SELECT role FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()

    if not row or row["role"] != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado. Necessário role 'admin'.")
    return email


# =========================
# ROTAS — Admin
# =========================

@app.get("/admin/stats", tags=["admin"])
def admin_stats_global(email: str = Depends(verificar_admin)):
    """Estatísticas globais do sistema (somente admin)."""
    conn = conectar()
    try:
        geral = conn.execute("""
            SELECT
                COUNT(*)                    AS total_analises,
                SUM(status = 'PASS')        AS total_aprovadas,
                SUM(status = 'WARNING')     AS total_alertas,
                SUM(status = 'FAIL')        AS total_falhas,
                ROUND(AVG(score), 2)        AS score_medio,
                ROUND(AVG(tempo_ms), 2)     AS tempo_medio_ms,
                COUNT(DISTINCT usuario_email) AS total_usuarios_ativos
            FROM analises
        """).fetchone()

        total_usuarios = conn.execute(
            "SELECT COUNT(*) AS total FROM usuarios"
        ).fetchone()["total"]

        # Ranking de usuários por volume de análises
        ranking = conn.execute("""
            SELECT
                u.nome,
                a.usuario_email,
                COUNT(*) AS total,
                SUM(a.status = 'PASS')    AS aprovadas,
                SUM(a.status = 'FAIL')    AS falhas,
                ROUND(AVG(a.score), 1)    AS score_medio,
                MAX(a.data_analise)       AS ultima_analise
            FROM analises a
            LEFT JOIN usuarios u ON u.email = a.usuario_email
            GROUP BY a.usuario_email
            ORDER BY total DESC
            LIMIT 20
        """).fetchall()

        # Evolução global dos últimos 14 dias
        evolucao = conn.execute("""
            SELECT
                DATE(data_analise)      AS dia,
                COUNT(*)                AS total,
                SUM(status = 'PASS')    AS aprovadas,
                SUM(status = 'FAIL')    AS falhas
            FROM analises
            WHERE data_analise >= datetime('now', '-14 days')
            GROUP BY dia
            ORDER BY dia
        """).fetchall()

        # Distribuição por tipo de tela (global)
        por_tela = conn.execute("""
            SELECT tipo_tela, COUNT(*) AS qtd
            FROM analises
            GROUP BY tipo_tela
            ORDER BY qtd DESC
        """).fetchall()

    finally:
        conn.close()

    total = geral["total_analises"] or 0
    return {
        "total_analises":       total,
        "total_aprovadas":      geral["total_aprovadas"]  or 0,
        "total_alertas":        geral["total_alertas"]    or 0,
        "total_falhas":         geral["total_falhas"]     or 0,
        "taxa_aprovacao":       round((geral["total_aprovadas"] or 0) / total * 100, 1) if total else 0,
        "score_medio":          geral["score_medio"],
        "tempo_medio_ms":       geral["tempo_medio_ms"],
        "total_usuarios":       total_usuarios,
        "total_usuarios_ativos": geral["total_usuarios_ativos"] or 0,
        "ranking_usuarios": [
            {
                "nome":          r["nome"] or r["usuario_email"].split("@")[0],
                "email":         r["usuario_email"],
                "total":         r["total"],
                "aprovadas":     r["aprovadas"] or 0,
                "falhas":        r["falhas"]    or 0,
                "score_medio":   r["score_medio"],
                "ultima_analise": r["ultima_analise"],
            }
            for r in ranking
        ],
        "evolucao_14dias": [
            {"dia": e["dia"], "total": e["total"], "aprovadas": e["aprovadas"], "falhas": e["falhas"]}
            for e in evolucao
        ],
        "por_tipo_tela": [
            {"tipo_tela": t["tipo_tela"], "label": formatar_tipo_tela(t["tipo_tela"] or "UNKNOWN"), "qtd": t["qtd"]}
            for t in por_tela
        ],
    }


@app.get("/admin/usuarios", tags=["admin"])
def admin_listar_usuarios(
    email: str = Depends(verificar_admin),
    limite: int = 50,
    offset: int = 0,
):
    """Lista todos os usuários cadastrados (somente admin)."""
    conn = conectar()
    try:
        # Busca usuários sem JOIN para compatibilidade com Turso
        rows = conn.execute("""
            SELECT id, nome, email, telefone, role,
                   receber_relatorios, criado_em,
                   criado_por, ultimo_login
            FROM usuarios
            ORDER BY criado_em DESC
            LIMIT ? OFFSET ?
        """, (min(limite, 100), offset)).fetchall()

        total = conn.execute(
            "SELECT COUNT(*) AS c FROM usuarios"
        ).fetchone()["c"]

        # Conta análises separadamente para cada usuário
        contagem = {}
        for r in rows:
            cur = conn.execute(
                "SELECT COUNT(*) AS total FROM analises WHERE usuario_email = ?",
                (r["email"],)
            ).fetchone()
            contagem[r["email"]] = cur["total"] if cur else 0

    finally:
        conn.close()

    return {
        "total": total,
        "usuarios": [
            {
                "id":                 r["id"],
                "nome":               r["nome"] or "",
                "email":              r["email"],
                "telefone":           r["telefone"] or "",
                "role":               r["role"],
                "receber_relatorios": bool(r["receber_relatorios"]),
                "criado_em":          r["criado_em"] or "",
                "ativo":              True,
                "criado_por":         r["criado_por"] or "—",
                "ultimo_login":       r["ultimo_login"] if r["ultimo_login"] else None,
                "total_analises":     contagem.get(r["email"], 0),
            }
            for r in rows
        ],
    }

class AdminCriarUsuario(BaseModel):
    nome: str
    email: str
    senha: str
    telefone: Optional[str] = None
    role: str = "QA Analyst"

@app.post("/admin/usuarios/criar", tags=["admin"])
def admin_criar_usuario(
    data: AdminCriarUsuario,
    admin_email: str = Depends(verificar_admin),
):
    """Cria um novo usuário diretamente (somente admin, sem convite)."""
    if data.role not in ROLES_VALIDAS:
        raise HTTPException(status_code=400, detail=f"Role inválido. Use: {ROLES_VALIDAS}")
    if not senha_forte(data.senha):
        raise HTTPException(status_code=400, detail="Senha fraca.")
    conn = conectar()
    try:
        conn.execute(
            "INSERT INTO usuarios (nome, email, senha, telefone, role) VALUES (?, ?, ?, ?, ?)",
            (data.nome, data.email.lower(), pwd_context.hash(data.senha), data.telefone, data.role)
        )
        conn.commit()
        return {"msg": f"Usuário {data.email} criado com role '{data.role}'."}
    except Exception as _e:
        if "UNIQUE" not in str(_e) and "unique" not in str(_e): raise
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
    finally:
        conn.close()

@app.put("/admin/usuarios/{usuario_email}/role", tags=["admin"])
def admin_alterar_role(
    usuario_email: str,
    novo_role: str,
    admin_email: str = Depends(verificar_admin),
):
    """Altera o role de um usuário (somente admin)."""
    if novo_role not in ROLES_VALIDAS:
        raise HTTPException(
            status_code=400,
            detail=f"Role inválido. Use: {', '.join(sorted(ROLES_VALIDAS))}"
        )
    if usuario_email == admin_email:
        raise HTTPException(status_code=400, detail="Você não pode alterar seu próprio role.")

    conn = conectar()
    try:
        cur = conn.execute(
            "UPDATE usuarios SET role = ? WHERE email = ?",
            (novo_role, usuario_email)
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    finally:
        conn.close()

    return {"msg": f"Role de '{usuario_email}' alterado para '{novo_role}'."}


@app.delete("/admin/usuarios/{usuario_email}", tags=["admin"])
def admin_remover_usuario(
    usuario_email: str,
    admin_email: str = Depends(verificar_admin),
):
    """Remove um usuário e todo o seu histórico (somente admin)."""
    if usuario_email == admin_email:
        raise HTTPException(status_code=400, detail="Você não pode remover sua própria conta.")

    conn = conectar()
    try:
        conn.execute("DELETE FROM analises WHERE usuario_email = ?", (usuario_email,))
        cur = conn.execute("DELETE FROM usuarios WHERE email = ?", (usuario_email,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    finally:
        conn.close()

    return {"msg": f"Usuário '{usuario_email}' removido com sucesso."}


@app.get("/admin/historico", tags=["admin"])
def admin_historico_global(
    email: str = Depends(verificar_admin),
    limite: int = 100,
    offset: int = 0,
    status_filtro: Optional[str] = None,
):
    """Histórico global de todas as análises, com filtro opcional por status."""
    validos = {"PASS", "WARNING", "FAIL", None}
    if status_filtro not in validos:
        raise HTTPException(status_code=400, detail="status_filtro deve ser PASS, WARNING ou FAIL.")

    conn = conectar()
    try:
        query = """
            SELECT a.nome_arquivo, a.status, a.score, a.tipo_tela,
                   a.classe_predita, a.tempo_ms, a.data_analise,
                   u.nome, a.usuario_email
            FROM analises a
            LEFT JOIN usuarios u ON u.email = a.usuario_email
            {}
            ORDER BY a.data_analise DESC
            LIMIT ? OFFSET ?
        """.format("WHERE a.status = ?" if status_filtro else "")

        params = ([status_filtro] if status_filtro else []) + [min(limite, 200), offset]
        rows = conn.execute(query, params).fetchall()
    finally:
        conn.close()

    return [
        {
            "usuario_nome":   row["nome"] or row["usuario_email"].split("@")[0],
            "usuario_email":  row["usuario_email"],
            "nome_arquivo":   row["nome_arquivo"],
            "status":         row["status"],
            "score":          row["score"],
            "tipo_tela":      formatar_tipo_tela(row["tipo_tela"] or "UNKNOWN"),
            "classe_predita": row["classe_predita"],
            "tempo_ms":       row["tempo_ms"],
            "data_analise":   row["data_analise"],
        }
        for row in rows
    ]
