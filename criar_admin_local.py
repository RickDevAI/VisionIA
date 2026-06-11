from passlib.context import CryptContext
import sqlite3

conn = sqlite3.connect('usuarios.db')
conn.execute('''CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    email TEXT UNIQUE,
    senha TEXT,
    telefone TEXT,
    receber_relatorios INTEGER DEFAULT 1,
    role TEXT DEFAULT "QA Analyst"
)''')

hash_senha = CryptContext(schemes=['bcrypt']).hash('Admin@123')
conn.execute(
    "INSERT OR IGNORE INTO usuarios (nome, email, senha, role) VALUES (?, ?, ?, ?)",
    ('Admin', 'admin@local.com', hash_senha, 'admin')
)
conn.commit()
conn.close()
print('Admin local criado!')
print('Email: admin@local.com')
print('Senha: Admin@123')
