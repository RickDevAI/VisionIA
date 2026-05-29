from passlib.context import CryptContext
import sqlite3
import os

# Garante que roda na pasta certa
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "usuarios.db")

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Cria tabela se não existir
conn.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id                 INTEGER PRIMARY KEY AUTOINCREMENT,
        nome               TEXT,
        email              TEXT UNIQUE NOT NULL,
        senha              TEXT NOT NULL,
        telefone           TEXT,
        receber_relatorios INTEGER DEFAULT 0,
        role               TEXT DEFAULT 'QA Analyst',
        criado_em          TEXT DEFAULT (datetime('now'))
    )
""")

email = "admin@visionia.com"
senha = "Admin@1234"

cur = conn.execute(
    "INSERT OR IGNORE INTO usuarios (nome, email, senha, role) VALUES (?, ?, ?, ?)",
    ("Admin", email, pwd.hash(senha), "admin")
)
conn.commit()

if cur.rowcount > 0:
    print(f"\n✅ Admin criado com sucesso!")
    print(f"   Email: {email}")
    print(f"   Senha: {senha}")
else:
    # Atualiza role se usuário já existe
    conn.execute("UPDATE usuarios SET role = 'admin' WHERE email = ?", (email,))
    conn.commit()
    print(f"\n✅ Usuário já existia — role atualizado para admin.")
    print(f"   Email: {email}")
    print(f"   Senha: {senha}")

# Confirma no banco
row = conn.execute("SELECT nome, email, role FROM usuarios WHERE email = ?", (email,)).fetchone()
print(f"\n   Confirmado no banco: {row['nome']} | {row['email']} | {row['role']}")
conn.close()
