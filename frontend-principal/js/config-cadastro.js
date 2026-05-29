// =============================================
//  MODO PÚBLICO (padrão):
//    Qualquer pessoa pode se cadastrar livremente
//    Role padrão: QA Analyst
//    Após cadastro → volta para login.html
//
//  MODO ADMIN:
//    Admin acessa cadastro.html?modo=admin (via painel)
//    Pode definir o role do novo usuário
//    Usa endpoint /admin/usuarios/criar (com token JWT)
//    Após cadastro → volta para admin.html
//
//  NOTA: Sistema de convites está planejado para versão futura.
// =============================================

const _params    = new URLSearchParams(window.location.search);
const _modoAdmin = _params.get("modo") === "admin";

document.addEventListener("DOMContentLoaded", () => {
  configurarModo();
  configurarListeners();
  const senhaInput = document.getElementById("senha");
  if (senhaInput) senhaInput.addEventListener("input", atualizarIndicadorSenha);
});

function configurarModo() {
  const badge     = document.getElementById("badgeModo");
  const subtitulo = document.getElementById("subtituloCadastro");
  const campoConv = document.getElementById("campoConvite");
  const campoRole = document.getElementById("campoRole");
  const btnSalvar = document.getElementById("btnSalvar");
  const btnVoltar = document.getElementById("btnVoltar");

  if (campoConv) campoConv.style.display = "none";

  if (_modoAdmin) {
    if (badge)     { badge.textContent = "Admin"; badge.className = "badge-modo badge-admin"; }
    if (subtitulo) subtitulo.textContent = "Criando usuário como administrador. O convite não é necessário.";
    if (campoRole) campoRole.style.display = "block";
    if (btnSalvar) btnSalvar.textContent = "Criar usuário";
    if (btnVoltar) btnVoltar.textContent  = "Voltar ao painel";
  } else {
    if (badge)     { badge.textContent = "Cadastro"; badge.className = "badge-modo badge-convite"; }
    if (subtitulo) subtitulo.textContent = "Preencha seus dados para criar sua conta.";
    if (campoRole) campoRole.style.display = "none";
    if (btnSalvar) btnSalvar.textContent = "Criar conta";
    if (btnVoltar) btnVoltar.textContent  = "Voltar ao login";
  }
}

function voltarAoOrigem() {
  window.location.href = _modoAdmin ? "admin.html" : "login.html";
}

function mostrarMensagemCadastro(texto, erro = false) {
  const msg = document.getElementById("mensagemCadastro");
  if (!msg) return;
  msg.innerText   = texto;
  msg.style.color = erro ? "#b42318" : "#166534";
}

function setCadastroLoading(ativo) {
  document.querySelectorAll(".btn-green").forEach(b => {
    b.disabled      = ativo;
    b.style.opacity = ativo ? "0.7" : "1";
    b.style.cursor  = ativo ? "not-allowed" : "pointer";
  });
}

function validarEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function limparFormularioCadastro() {
  ["nome", "email", "telefone", "senha", "confirmar-senha"]
    .forEach(id => { const el = document.getElementById(id); if (el) el.value = ""; });
}

async function salvarCadastro() {
  const nome           = document.getElementById("nome")?.value.trim()               || "";
  const email          = document.getElementById("email")?.value.trim().toLowerCase() || "";
  const telefone       = document.getElementById("telefone")?.value.trim()            || "";
  const senha          = document.getElementById("senha")?.value                      || "";
  const confirmarSenha = document.getElementById("confirmar-senha")?.value            || "";

  mostrarMensagemCadastro("");

  if (!nome || !email || !senha || !confirmarSenha) {
    mostrarMensagemCadastro("Preencha todos os campos obrigatórios.", true); return;
  }
  if (!validarEmail(email)) {
    mostrarMensagemCadastro("Digite um e-mail válido.", true); return;
  }
  if (!senhaEhValida(senha)) {
    mostrarMensagemCadastro("A senha deve ter mínimo 8 caracteres com maiúscula, minúscula, número e caractere especial.", true); return;
  }
  if (senha !== confirmarSenha) {
    mostrarMensagemCadastro("As senhas não coincidem.", true); return;
  }

  setCadastroLoading(true);

  try {
    let res;

    if (_modoAdmin) {
      const token = localStorage.getItem("token");
      if (!token) { window.location.href = "login.html"; return; }
      const role = document.getElementById("novoRole")?.value || "QA Analyst";
      res = await fetch(`${API_URL}/admin/usuarios/criar`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ nome, email, telefone: telefone || null, senha, role })
      });
    } else {
      res = await fetch(`${API_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome, email, telefone: telefone || null, senha })
      });
    }

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      mostrarMensagemCadastro(data.detail || "Erro ao criar usuário.", true); return;
    }

    mostrarMensagemCadastro(_modoAdmin ? `Usuário ${email} criado com sucesso!` : "Conta criada! Redirecionando...");
    limparFormularioCadastro();
    setTimeout(() => { window.location.href = _modoAdmin ? "admin.html" : "login.html"; }, 1200);

  } catch (error) {
    console.error("Erro no cadastro:", error);
    mostrarMensagemCadastro("Não foi possível conectar ao servidor.", true);
  } finally {
    setCadastroLoading(false);
  }
}

function configurarListeners() {
  ["nome", "email", "telefone", "senha", "confirmar-senha"].forEach(id => {
    const campo = document.getElementById(id);
    if (!campo) return;
    campo.addEventListener("keypress", e => { if (e.key === "Enter") salvarCadastro(); });
  });
}

function validarRegrasSenha(senha) {
  return {
    length:  senha.length >= 8,
    upper:   /[A-Z]/.test(senha),
    lower:   /[a-z]/.test(senha),
    number:  /\d/.test(senha),
    special: /[^A-Za-z0-9]/.test(senha)
  };
}

function senhaEhValida(senha) {
  const r = validarRegrasSenha(senha);
  return r.length && r.upper && r.lower && r.number && r.special;
}

function atualizarIndicadorSenha() {
  const senha = document.getElementById("senha")?.value || "";
  const regras = validarRegrasSenha(senha);
  [["ruleLength", regras.length], ["ruleUpper", regras.upper],
   ["ruleLower",  regras.lower],  ["ruleNumber", regras.number],
   ["ruleSpecial", regras.special]].forEach(([id, ok]) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove("valid", "invalid");
    if (senha) el.classList.add(ok ? "valid" : "invalid");
  });
}
