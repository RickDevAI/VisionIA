// =============================================
//  MODO CONVITE (padrão):
//    Usuário acessa cadastro.html?convite=XXXX-XXXX-XXXX
//    Preenche dados + código de convite vem preenchido
//    Após cadastro → volta para login.html
//
//  MODO ADMIN:
//    Admin acessa cadastro.html?modo=admin (via painel)
//    Campo convite fica oculto
//    Usa endpoint /admin/usuarios/criar (com token JWT)
//    Após cadastro → volta para admin.html
// =============================================

// ── Detecta modo e parâmetros da URL ──
const _params    = new URLSearchParams(window.location.search);
const _modoAdmin = _params.get("modo") === "admin";
const _conviteURL = _params.get("convite") || "";

// ── Inicialização ──
document.addEventListener("DOMContentLoaded", () => {
  if (!_modoAdmin) {
    const token = localStorage.getItem("token");
    const role  = (JSON.parse(localStorage.getItem("user") || "{}")).role;
  }

  configurarModo();
  configurarListeners();

  const senhaInput = document.getElementById("senha");
  if (senhaInput) senhaInput.addEventListener("input", atualizarIndicadorSenha);
});

function configurarModo() {
  const badge      = document.getElementById("badgeModo");
  const subtitulo  = document.getElementById("subtituloCadastro");
  const campoConv  = document.getElementById("campoConvite");
  const btnSalvar  = document.getElementById("btnSalvar");
  const btnVoltar  = document.getElementById("btnVoltar");

  const campoRole = document.getElementById("campoRole");

  if (_modoAdmin) {
    if (badge)     { badge.textContent = "Admin"; badge.className = "badge-modo badge-admin"; }
    if (subtitulo) subtitulo.textContent = "Criando usuário como administrador.";
    if (campoConv) campoConv.style.display = "none"; 
    if (campoRole) campoRole.style.display = "block"; 
    if (btnSalvar) btnSalvar.textContent = "Criar usuário";
    if (btnVoltar) btnVoltar.textContent  = "Voltar ao painel";
  } else {
    if (badge)     { badge.textContent = "Convite"; badge.className = "badge-modo badge-convite"; }
    if (subtitulo) subtitulo.textContent = "Preencha seus dados e informe o código de convite recebido.";
    if (campoRole) campoRole.style.display = "none";  
    if (campoConv) campoConv.style.display = "block"; 
    if (btnSalvar) btnSalvar.textContent = "Criar conta";
    if (btnVoltar) btnVoltar.textContent  = "Voltar ao login";

    const campoCodigo = document.getElementById("codigo-convite");
    if (campoCodigo && _conviteURL) {
      campoCodigo.value    = _conviteURL.toUpperCase();
      campoCodigo.readOnly = true;
      campoCodigo.style.background = "#f0f4fa";
    }
  }
}

function voltarAoOrigem() {
  window.location.href = _modoAdmin ? "admin.html" : "login.html";
}

function mostrarMensagemCadastro(texto, erro = false) {
  const msg = document.getElementById("mensagemCadastro");
  if (!msg) return;
  msg.innerText  = texto;
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
  ["nome", "email", "telefone", "senha", "confirmar-senha", "codigo-convite"]
    .forEach(id => { const el = document.getElementById(id); if (el) el.value = ""; });
}

async function salvarCadastro() {
  const nome           = document.getElementById("nome")?.value.trim()           || "";
  const email          = document.getElementById("email")?.value.trim().toLowerCase() || "";
  const telefone       = document.getElementById("telefone")?.value.trim()       || "";
  const senha          = document.getElementById("senha")?.value                 || "";
  const confirmarSenha = document.getElementById("confirmar-senha")?.value       || "";
  const codigoConvite  = (document.getElementById("codigo-convite")?.value || "").trim().toUpperCase();

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
  if (!_modoAdmin && !codigoConvite) {
    mostrarMensagemCadastro("Informe o código de convite.", true); return;
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
        body: JSON.stringify({ nome, email, telefone: telefone || null, senha, codigo_convite: codigoConvite })
      });
    }

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      mostrarMensagemCadastro(data.detail || "Erro ao criar usuário.", true); return;
    }

    mostrarMensagemCadastro(_modoAdmin ? `Usuário ${email} criado com sucesso!` : "Conta criada! Redirecionando...");
    limparFormularioCadastro();

    setTimeout(() => {
      window.location.href = _modoAdmin ? "admin.html" : "login.html";
    }, 1200);

  } catch (error) {
    console.error("Erro no cadastro:", error);
    mostrarMensagemCadastro("Não foi possível conectar ao servidor.", true);
  } finally {
    setCadastroLoading(false);
  }
}

function configurarListeners() {
  ["nome", "email", "telefone", "senha", "confirmar-senha", "codigo-convite"].forEach(id => {
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
