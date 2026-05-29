function getToken() {
  return localStorage.getItem("token");
}
function limparSessao() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
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
  window.location.href = "cadastro.html";
}
function esqueciSenha() {
  const email = prompt("Digite seu e-mail para recuperação:");
  if (!email) return;
  alert(
    "Funcionalidade em construção. Em uma versão futura, o sistema enviará instruções para redefinição de senha."
  );
}
async function validarSessaoExistente() {
  const token = getToken();
  if (!token) return;
  try {
    const res = await fetch(`${API_URL}/me`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    if (res.ok) {
      const data = await res.json();
      if (data.role === "admin") {
        window.location.href = "admin.html";
      } else {
        window.location.href = "index.html";
      }
      return;
    }
    if (res.status === 401) {
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
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, senha })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      mostrarErro(data.detail || "Erro ao fazer login.");
      return;
    }
    localStorage.setItem("token", data.token);
    localStorage.setItem(
      "user",
      JSON.stringify({
        nome: data.nome || "",
        email: data.email || email,
        role: data.role || "QA Analyst"
      })
    );
    if (data.role === "admin") {
      window.location.href = "admin.html";
    } else {
      window.location.href = "index.html";
    }
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
