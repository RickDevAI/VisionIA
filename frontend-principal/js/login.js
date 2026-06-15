function getToken() {
  return localStorage.getItem("token");
}

function limparSessao() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

function normalizarRole(role) {
  return String(role || "").trim().toLowerCase();
}

function isAdminRole(role) {
  const r = normalizarRole(role);
  return r === "admin" || r === "administrador";
}

function redirecionarPorRole(role) {
  if (isAdminRole(role)) {
    window.location.replace("/admin.html");
  } else {
    window.location.replace("/index.html");
  }
}

function mostrarLoading(ativo) {
  const loading = document.getElementById("loading");
  const botoes = document.querySelectorAll(".btn-login, .btn-register");

  if (loading) {
    loading.style.display = ativo ? "block" : "none";
  }

  botoes.forEach((botao) => {
    botao.disabled = ativo;
    botao.style.opacity = ativo ? "0.7" : "1";
    botao.style.cursor = ativo ? "not-allowed" : "pointer";
  });
}

function mostrarErro(mensagem = "") {
  const erro = document.getElementById("erro");

  if (erro) {
    erro.innerText = mensagem;
  } else if (mensagem) {
    alert(mensagem);
  }
}

function irCadastro() {
  window.location.href = "/cadastro.html";
}

async function esqueciSenha() {
  const email = prompt("Digite seu e-mail para recuperação:");
  if (!email) return;
  const res = await fetch(`${API_URL}/recuperar-senha`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email })
  });
  const data = await res.json().catch(() => ({}));
  alert(data.msg || "Verifique seu e-mail.");
}

async function validarSessaoExistente() {
  const token = getToken();

  if (!token) return;

  try {
    const res = await fetch(`${API_URL}/me`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    if (res.ok) {
      const data = await res.json();

      localStorage.setItem(
        "user",
        JSON.stringify({
          nome: data.nome || "",
          email: data.email || "",
          role: normalizarRole(data.role || "QA Analyst")
        })
      );

      redirecionarPorRole(data.role);
      return;
    }

    if (res.status === 401 || res.status === 403) {
      limparSessao();
    }
  } catch (error) {
    console.error("Não foi possível validar a sessão existente:", error);
  }
}

async function login() {
  const emailInput = document.getElementById("email");
  const senhaInput = document.getElementById("senha");

  const email = emailInput?.value.trim().toLowerCase() || "";
  const senha = senhaInput?.value || "";

  mostrarErro("");

  if (!email || !senha) {
    mostrarErro("Preencha e-mail e senha.");
    return;
  }

  mostrarLoading(true);

  try {
    const res = await fetch(`${API_URL}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email, senha })
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      console.error("Erro no login:", res.status, data);
      mostrarErro(data.detail || "Erro ao fazer login.");
      return;
    }

    if (!data.token) {
      mostrarErro("Login realizado, mas o token não foi retornado pela API.");
      return;
    }

    const role = normalizarRole(data.role || "QA Analyst");

    localStorage.setItem("token", data.token);
    localStorage.setItem(
      "user",
      JSON.stringify({
        nome: data.nome || "",
        email: data.email || email,
        role
      })
    );

    redirecionarPorRole(role);
  } catch (error) {
    console.error("Erro no login:", error);
    mostrarErro("Não foi possível conectar ao servidor.");
  } finally {
    mostrarLoading(false);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await validarSessaoExistente();

  const emailInput = document.getElementById("email");
  const senhaInput = document.getElementById("senha");

  [emailInput, senhaInput].forEach((input) => {
    if (!input) return;

    input.addEventListener("keypress", function (event) {
      if (event.key === "Enter") {
        login();
      }
    });
  });
});
