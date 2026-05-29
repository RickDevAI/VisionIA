function getToken() {
  return localStorage.getItem("token");
}

function getUserLocal() {
  try {
    return JSON.parse(localStorage.getItem("user") || "{}");
  } catch {
    return {};
  }
}

function salvarUserLocal(user) {
  localStorage.setItem("user", JSON.stringify(user));
}

function limparSessao() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

function gerarIniciais(texto) {
  if (!texto) return "US";

  const partes = texto.trim().split(" ").filter(Boolean);

  if (partes.length === 1) {
    return partes[0].substring(0, 2).toUpperCase();
  }

  return (partes[0][0] + partes[1][0]).toUpperCase();
}

function atualizarCabecalhoUsuario({ nome = "", email = "", role = "QA Analyst" }) {
  const nomeExibicao = nome || email || "Usuário";

  const userName = document.getElementById("userName");
  const userRole = document.getElementById("userRole");
  const userAvatar = document.getElementById("userAvatar");

  if (userName) userName.innerText = nomeExibicao;
  if (userRole) userRole.innerText = role;
  if (userAvatar) userAvatar.innerText = gerarIniciais(nomeExibicao);
}

function preencherFormulario(data, userLocal) {
  const nome = data.nome || userLocal.nome || "";
  const email = data.email || userLocal.email || "";
  const telefone = data.telefone || "";
  const receberRelatorios = !!data.receber_relatorios;
  const role = data.role || userLocal.role || "QA Analyst";

  atualizarCabecalhoUsuario({ nome, email, role });

  const nomeInput = document.getElementById("nome");
  const emailInput = document.getElementById("email");
  const telefoneInput = document.getElementById("telefone");
  const emailCheck = document.getElementById("emailCheck");

  if (nomeInput) nomeInput.value = nome;
  if (emailInput) emailInput.value = email;
  if (telefoneInput) telefoneInput.value = telefone;
  if (emailCheck) emailCheck.checked = receberRelatorios;

  salvarUserLocal({ nome, email, role });
}

function desabilitarPreferenciasNaoImplementadas() {
  const idsNaoImplementados = [
    "novidadesCheck",
    "lembretesCheck",
    "notifEmailCheck",
    "notifSistemaCheck"
  ];

  idsNaoImplementados.forEach((id) => {
    const el = document.getElementById(id);
    if (!el) return;

    el.checked = false;
    el.disabled = true;
    el.title = "Preferência ainda não implementada no backend.";
  });
}

async function carregarUsuario() {
  const token = getToken();
  const userLocal = getUserLocal();

  if (!token) {
    window.location.href = "login.html";
    return;
  }

  if (userLocal.email || userLocal.nome) {
    atualizarCabecalhoUsuario(userLocal);
  }

  try {
    const res = await fetch(`${API_URL}/me`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    if (res.status === 401) {
      limparSessao();
      window.location.href = "login.html";
      return;
    }

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new Error(data.detail || "Erro ao carregar usuário");
    }

    preencherFormulario(data, userLocal);
  } catch (error) {
    console.error("Erro ao carregar perfil:", error);

    if (userLocal.email || userLocal.nome) {
      preencherFormulario(userLocal, userLocal);
    }

    alert("Não foi possível carregar as configurações do servidor.");
  }
}

async function salvarPerfil() {
  const token = getToken();

  if (!token) {
    window.location.href = "login.html";
    return;
  }

  const nome = document.getElementById("nome")?.value.trim() || "";
  const email = document.getElementById("email")?.value.trim().toLowerCase() || "";
  const telefone = document.getElementById("telefone")?.value.trim() || "";
  const emailCheck = !!document.getElementById("emailCheck")?.checked;

  if (!email) {
    alert("O e-mail é obrigatório.");
    return;
  }

  const userAntes = getUserLocal();
  const emailAntigo = userAntes.email || "";

  try {
    const res = await fetch(`${API_URL}/me`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        nome,
        email,
        telefone,
        receber_relatorios: emailCheck
      })
    });

    if (res.status === 401) {
      alert("Sessão expirada. Faça login novamente.");
      limparSessao();
      window.location.href = "login.html";
      return;
    }

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new Error(data.detail || "Erro ao salvar perfil");
    }

    if (data.token) {
      localStorage.setItem("token", data.token);
    }

    const userAtualizado = {
      ...userAntes,
      nome,
      email,
      role: userAntes.role || "QA Analyst"
    };

    salvarUserLocal(userAtualizado);
    atualizarCabecalhoUsuario(userAtualizado);

    if (email !== emailAntigo && !data.token) {
      alert("Perfil atualizado com sucesso. Faça login novamente.");
      limparSessao();
      window.location.href = "login.html";
      return;
    }

    alert("Perfil atualizado com sucesso!");
  } catch (error) {
    console.error("Erro ao salvar perfil:", error);
    alert(error.message || "Não foi possível salvar as configurações.");
  }
}

function abrirSuporte() {
  alert("Em breve: integração com suporte real.");
}

function voltarInicio() {
  window.location.href = "index.html";
}

function logout() {
  limparSessao();
  window.location.href = "login.html";
}

function toggleMenu() {
  const menu = document.getElementById("userMenu");
  if (menu) {
    menu.classList.toggle("active");
  }
}

function enviarFeedback() {
  const feedback = document.getElementById("feedbackTexto");
  const texto = feedback?.value.trim() || "";

  if (!texto) {
    alert("Digite um feedback antes de enviar.");
    return;
  }

  alert("Feedback registrado. A persistência desse recurso ainda não foi implementada.");
  feedback.value = "";
}

document.addEventListener("click", function (e) {
  const userBox = document.querySelector(".user-access");
  const menu = document.getElementById("userMenu");

  if (!userBox || !menu) return;

  if (!userBox.contains(e.target)) {
    menu.classList.remove("active");
  }
});

document.addEventListener("DOMContentLoaded", () => {
  desabilitarPreferenciasNaoImplementadas();
  carregarUsuario();
});