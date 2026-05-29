let arquivos = [];

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

function escaparHtml(valor) {
  return String(valor).replace(/[&<>"']/g, (char) => {
    const mapa = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    };
    return mapa[char];
  });
}

function atualizarCabecalhoUsuario(user) {
  const nome = user.nome || "";
  const email = user.email || "Usuário";
  const role = user.role || "QA Analyst";
  const nomeExibicao = nome || email;

  const userName = document.getElementById("userName");
  const userRole = document.getElementById("userRole");
  const userAvatar = document.getElementById("userAvatar");

  if (userName) userName.textContent = nomeExibicao;
  if (userRole) userRole.textContent = role;
  if (userAvatar) userAvatar.textContent = gerarIniciais(nomeExibicao);

  const adminLink = document.getElementById("adminLink");
  if (adminLink) adminLink.style.display = role === "admin" ? "block" : "none";
}

async function carregarUsuarioDashboard() {
  const token = getToken();
  if (!token) {
    window.location.href = "login.html";
    return false;
  }

  const userLocal = getUserLocal();
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
      alert("Sessão expirada. Faça login novamente.");
      limparSessao();
      window.location.href = "login.html";
      return false;
    }

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new Error(data.detail || "Erro ao carregar usuário.");
    }

    const user = {
      nome: data.nome || "",
      email: data.email || userLocal.email || "",
      role: data.role || userLocal.role || "QA Analyst"
    };

    salvarUserLocal(user);
    atualizarCabecalhoUsuario(user);
    return true;
  } catch (error) {
    console.error("Erro ao carregar usuário:", error);

    if (userLocal.email || userLocal.nome) {
      atualizarCabecalhoUsuario(userLocal);
      return true;
    }

    return false;
  }
}

function abrirScreenshots() {
  const input = document.getElementById("uploadScreenshots");
  if (!input) return;

  input.value = "";
  input.click();
}

function renderResultadoInicial() {
  const resultado = document.getElementById("resultado");
  if (!resultado) return;

  resultado.innerHTML = `
    <div class="comment-header">
      <div class="bot">IA</div>
      <strong>IA Bot</strong>
      <span class="badge">Aguardando nova análise</span>
    </div>
    <div class="small">Nenhuma screenshot carregada no momento.</div>
  `;
}

function classeStatusItem(status) {
  if (status === "PASS") return "ok";
  if (status === "WARNING") return "warn";
  return "fail";
}

function classeBadgeStatus(status) {
  if (status === "PASS") return "green";
  if (status === "WARNING") return "yellow";
  return "red";
}

function classeBadgeScore(score, status) {
  if (status === "PASS") {
    if (score >= 80) return "green";
    if (score >= 60) return "yellow";
    return "red";
  }

  if (status === "WARNING") {
    return "yellow";
  }

  if (status === "FAIL") {
    if (score >= 80) return "red";
    if (score >= 60) return "yellow";
    return "red";
  }

  return "red";
}

function textoStatusFinal(status) {
  if (status === "PASS") return "Screenshot aprovada na pré-validação da IA";
  if (status === "WARNING") return "Screenshot sinalizada para revisão pela IA";
  return "Screenshot reprovada na pré-validação da IA";
}

function gerarResumoFinal({ analisadas, aprovadas, alertas, falhas }) {
  if (analisadas === 0) {
    return "Nenhuma screenshot pôde ser analisada.";
  }

  if (falhas > 0) {
    return `A IA identificou ${falhas} screenshot(s) como inválida(s), ${alertas} com alerta e ${aprovadas} válida(s).`;
  }

  if (alertas > 0) {
    return `A IA sinalizou ${alertas} screenshot(s) para revisão e aprovou ${aprovadas}.`;
  }

  return `A IA aprovou ${aprovadas} screenshot(s) na pré-validação.`;
}

function formatarTempoAnalise(ms) {
  if (ms < 1000) {
    return `${Math.round(ms)} ms`;
  }

  return `${(ms / 1000).toFixed(2).replace(".", ",")} s`;
}

function listarItensNaturais(itens) {
  if (!Array.isArray(itens) || itens.length === 0) return "";

  if (itens.length === 1) return itens[0];
  if (itens.length === 2) return `${itens[0]} e ${itens[1]}`;

  return `${itens.slice(0, -1).join(", ")} e ${itens[itens.length - 1]}`;
}

function gerarComentarioValidacao({ status, tipoTela, problemas = [], detectados = [] }) {
  const tela = tipoTela || "desconhecida";

  if (status === "PASS") {
    if (detectados.length > 0) {
      return `A IA considerou a screenshot válida porque encontrou ${listarItensNaturais(detectados)} dentro do padrão esperado para a tela ${tela}.`;
    }

    return `A IA considerou a screenshot válida porque ela está dentro do padrão visual esperado para a tela ${tela}.`;
  }

  if (status === "WARNING") {
    if (problemas.length > 0) {
      return `A IA sinalizou a screenshot para revisão porque identificou ${listarItensNaturais(problemas)}.`;
    }

    return `A IA sinalizou a screenshot para revisão porque encontrou possíveis inconsistências na tela ${tela}.`;
  }

  if (problemas.length > 0) {
    return `A IA considerou a screenshot inválida porque identificou ${listarItensNaturais(problemas)}.`;
  }

  return `A IA considerou a screenshot inválida porque ela está fora do padrão visual esperado para a tela ${tela}.`;
}

function toggleMenu() {
  const menu = document.getElementById("userMenu");
  if (menu) {
    menu.classList.toggle("active");
  }
}

function logout() {
  limparSessao();
  window.location.href = "login.html";
}

function irConfig() {
  window.location.href = "config.html";
}

function limparScreenshots() {
  if (arquivos.length === 0) return;

  const confirmar = confirm("Deseja remover todas as screenshots carregadas?");
  if (!confirmar) return;

  arquivos = [];

  const input = document.getElementById("uploadScreenshots");
  const previewArea = document.getElementById("attachmentsPreview");

  if (input) input.value = "";
  if (previewArea) previewArea.innerHTML = "";

  renderResultadoInicial();
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function animarBarraSuave(barra, de, ate, duracao = 700) {
  const inicio = performance.now();

  return new Promise((resolve) => {
    function frame(agora) {
      const progresso = Math.min((agora - inicio) / duracao, 1);
      const valorAtual = de + (ate - de) * progresso;

      barra.style.width = `${valorAtual}%`;

      if (progresso < 1) {
        requestAnimationFrame(frame);
      } else {
        resolve();
      }
    }

    requestAnimationFrame(frame);
  });
}

function iniciarTextoCarregando(elemento) {
  const mensagens = [
    "Carregando análise.",
    "Carregando análise..",
    "Carregando análise..."
  ];

  let indice = 0;

  const intervalo = setInterval(() => {
    if (!elemento) return;
    elemento.textContent = mensagens[indice];
    indice = (indice + 1) % mensagens.length;
  }, 450);

  return intervalo;
}

function pararTextoCarregando(intervalo) {
  clearInterval(intervalo);
}

async function rodarAnalise() {
  if (arquivos.length === 0) {
    alert("Selecione pelo menos uma screenshot.");
    return;
  }

  const token = getToken();
  if (!token) {
    window.location.href = "login.html";
    return;
  }

  const resultado = document.getElementById("resultado");
  if (!resultado) return;

  resultado.innerHTML = `
    <div class="comment-header">
      <div class="bot">IA</div>
      <strong>IA Bot</strong>
      <span class="badge yellow" id="statusBadge">Processando screenshots...</span>
      <span class="badge" id="scoreBadge" style="display:none;"></span>
      <span class="badge" id="countBadge" style="display:none;"></span>
    </div>

    <div class="progress-wrapper">
      <div id="barraProgresso" class="progress-bar"></div>
    </div>

    <div id="resumoTexto" style="margin-top:10px;">
      Carregando análise...
    </div>

    <div class="small" id="runInfo" style="display:none; margin-top:8px;"></div>

    <div id="logAnalise" style="margin-top:15px;"></div>
  `;

  const log = document.getElementById("logAnalise");
  const barra = document.getElementById("barraProgresso");
  const statusBadge = document.getElementById("statusBadge");
  const scoreBadge = document.getElementById("scoreBadge");
  const countBadge = document.getElementById("countBadge");
  const resumoTexto = document.getElementById("resumoTexto");
  const runInfo = document.getElementById("runInfo");

  const loadingInterval = iniciarTextoCarregando(resumoTexto);

  let progressoAtual = 0;
  let scoreTotal = 0;
  let analisadas = 0;
  let aprovadas = 0;
  let alertas = 0;
  let falhas = 0;

  try {
    for (let i = 0; i < arquivos.length; i++) {
      const file = arquivos[i];
      const inicioAnalise = performance.now();
      const blocosParaAdicionar = [];

      statusBadge.className = "badge yellow";
      statusBadge.textContent = `Validando screenshot ${i + 1} de ${arquivos.length}...`;

      try {
        const formData = new FormData();
        formData.append("file", file);

        const inicioRequisicao = performance.now();

        const response = await fetch(`${API_URL}/validar`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`
          },
          body: formData
        });

        if (response.status === 401) {
          alert("Sessão expirada. Faça login novamente.");
          limparSessao();
          window.location.href = "login.html";
          return;
        }

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
          throw new Error(data.detail || `Erro ${response.status}`);
        }

        const tempoAnaliseMs = performance.now() - inicioRequisicao;
        const tempoFormatado = formatarTempoAnalise(tempoAnaliseMs);

        const score = Number(data.score) || 0;
        const status = data.status || "FAIL";
        const tipoTela = data.tipo_tela || "UNKNOWN";
        const tipoTelaLabel = data.tipo_tela_label || "Não identificado";
        const resumo = data.resumo || "Sem resumo disponível";
        const detectados = Array.isArray(data.detectados) ? data.detectados : [];
        const problemas = Array.isArray(data.problemas) ? data.problemas : [];
        const comentarioValidacao =
          data.comentario_validacao ||
          gerarComentarioValidacao({
            status,
            tipoTela,
            problemas,
            detectados
          });

        analisadas++;
        scoreTotal += score;

        if (status === "PASS") {
          aprovadas++;
        } else if (status === "WARNING") {
          alertas++;
        } else {
          falhas++;
        }

        const blocoPrincipal = document.createElement("div");
        blocoPrincipal.className = `status-item ${classeStatusItem(status)}`;
        blocoPrincipal.innerHTML = `
          <strong>${escaparHtml(file.name)}</strong><br>
          Resultado: ${escaparHtml(status)}<br>
          Tela identificada pela IA: ${escaparHtml(tipoTelaLabel)}<br>
          Tempo de análise: ${escaparHtml(tempoFormatado)}<br>
          Comentário: ${escaparHtml(comentarioValidacao)}
        `;

        blocosParaAdicionar.push(blocoPrincipal);

        const blocoResumo = document.createElement("div");
        blocoResumo.className = `status-item ${classeStatusItem(status)}`;
        blocoResumo.innerHTML = `
          <strong>Resumo:</strong><br>
          ${escaparHtml(resumo)}
        `;
        blocosParaAdicionar.push(blocoResumo);

        if (detectados.length > 0) {
          const detect = document.createElement("div");
          detect.className = "status-item ok";
          detect.innerHTML = `
            <strong>Detectados:</strong><br>
            ${escaparHtml(detectados.join(", "))}
          `;
          blocosParaAdicionar.push(detect);
        }

        if (problemas.length > 0) {
          const problemasBloco = document.createElement("div");
          problemasBloco.className = "status-item warn";
          problemasBloco.innerHTML = `
            <strong>Problemas:</strong><br>
            ${problemas.map((p) => escaparHtml(p)).join("<br>")}
          `;
          blocosParaAdicionar.push(problemasBloco);
        }
      } catch (erro) {
        falhas++;

        const fail = document.createElement("div");
        fail.className = "status-item fail";
        fail.innerHTML = `
          <strong>${escaparHtml(file.name)}</strong><br>
          Erro: ${escaparHtml(erro.message)}
        `;
        blocosParaAdicionar.push(fail);
      } finally {
        const tempoMinimoArquivo = 1400;
        const tempoDecorrido = performance.now() - inicioAnalise;

        if (tempoDecorrido < tempoMinimoArquivo) {
          await sleep(tempoMinimoArquivo - tempoDecorrido);
        }

        statusBadge.className = "badge yellow";
        statusBadge.textContent = `Finalizando screenshot ${i + 1} de ${arquivos.length}...`;

        const proximoProgresso = ((i + 1) / arquivos.length) * 100;

        await animarBarraSuave(
          barra,
          progressoAtual,
          Math.min(proximoProgresso, 100),
          650
        );

        progressoAtual = proximoProgresso;

        blocosParaAdicionar.forEach((bloco) => {
          log.appendChild(bloco);
        });
      }
    }

    const scoreMedio = analisadas > 0 ? Math.round(scoreTotal / analisadas) : 0;

    let statusFinal = "FAIL";
    if (analisadas > 0 && falhas === 0 && alertas === 0) {
      statusFinal = "PASS";
    } else if (analisadas > 0 && falhas === 0 && alertas > 0) {
      statusFinal = "WARNING";
    }

    statusBadge.className = `badge ${classeBadgeStatus(statusFinal)}`;
    statusBadge.textContent = textoStatusFinal(statusFinal);

    scoreBadge.className = `badge ${classeBadgeScore(scoreMedio, statusFinal)}`;
    scoreBadge.style.display = "inline-flex";
    scoreBadge.textContent = `Score geral ${scoreMedio}%`;

    countBadge.className = "badge";
    countBadge.style.display = "inline-flex";
    countBadge.textContent = `Screenshots analisadas: ${analisadas}/${arquivos.length}`;

    resumoTexto.textContent = gerarResumoFinal({
      analisadas,
      aprovadas,
      alertas,
      falhas
    });

    runInfo.style.display = "block";
    runInfo.textContent = `Run ID: ${Date.now()} | Engine: visionia-validator`;
  } finally {
    pararTextoCarregando(loadingInterval);
  }
}

document.addEventListener("click", function (e) {
  const userBox = document.querySelector(".user-access");
  const menu = document.getElementById("userMenu");

  if (userBox && menu && !userBox.contains(e.target)) {
    menu.classList.remove("active");
  }
});

document.addEventListener("DOMContentLoaded", async () => {
  renderResultadoInicial();

  const ok = await carregarUsuarioDashboard();
  if (!ok && !getToken()) return;

  const uploadInput = document.getElementById("uploadScreenshots");
  if (!uploadInput || uploadInput.dataset.bound === "true") return;

  uploadInput.dataset.bound = "true";

  uploadInput.addEventListener("change", function (event) {
    const files = Array.from(event.target.files || []);
    const previewArea = document.getElementById("attachmentsPreview");
    const resultado = document.getElementById("resultado");

    if (!previewArea) return;

    arquivos = [];
    previewArea.innerHTML = "";

    for (const file of files) {
      arquivos.push(file);

      const reader = new FileReader();

      reader.onload = function (e) {
        const card = document.createElement("div");
        card.className = "attachment";

        const nome = document.createElement("div");
        nome.className = "attachment-name";
        nome.textContent = file.name;

        const tipo = document.createElement("div");
        tipo.className = "attachment-type";
        tipo.textContent = "Screenshot selecionada";

        const img = document.createElement("img");
        img.src = e.target.result;
        img.alt = file.name;

        card.appendChild(nome);
        card.appendChild(tipo);
        card.appendChild(img);
        previewArea.appendChild(card);
      };

      reader.readAsDataURL(file);
    }

    if (resultado) {
      resultado.innerHTML = `
        <div class="comment-header">
          <div class="bot">IA</div>
          <strong>IA Bot</strong>
          <span class="badge">Aguardando pré-validação</span>
        </div>
        <div class="small">
          ${arquivos.length} screenshot(s) selecionada(s). Clique em "Rodar Pré-validação" para iniciar a análise.
        </div>
      `;
    }
  });
});