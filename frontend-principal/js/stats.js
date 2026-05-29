async function carregarStats() {
  const token = getToken();
  if (!token) return;

  try {
    const res = await fetch(`${API_URL}/stats`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    if (!res.ok) return;

    const data = await res.json();
    renderizarStats(data);
  } catch (e) {
    console.error("Erro ao carregar stats:", e);
  }
}

function renderizarStats(data) {
  setTexto("statTotal",    data.total ?? 0);
  setTexto("statAprovadas", data.aprovadas ?? 0);
  setTexto("statAlertas",  data.alertas ?? 0);
  setTexto("statFalhas",   data.falhas ?? 0);
  setTexto("statTaxa",     `${data.taxa_aprovacao ?? 0}%`);
  setTexto("statScore",    data.score_medio != null ? `${data.score_medio}%` : "—");
  setTexto("statTempo",    data.tempo_medio_ms != null ? `${Math.round(data.tempo_medio_ms)} ms` : "—");

  const porTela = document.getElementById("statPorTela");
  if (porTela && Array.isArray(data.por_tipo_tela)) {
    porTela.innerHTML = data.por_tipo_tela.length === 0
      ? "<li>Nenhuma análise ainda.</li>"
      : data.por_tipo_tela
          .map(t => `<li><strong>${escHtml(t.label)}</strong>: ${t.qtd} análise(s)</li>`)
          .join("");
  }

  const evo = document.getElementById("statEvolucao");
  if (evo && Array.isArray(data.evolucao_7dias)) {
    if (data.evolucao_7dias.length === 0) {
      evo.innerHTML = "<p>Sem dados nos últimos 7 dias.</p>";
    } else {
      const max = Math.max(...data.evolucao_7dias.map(e => e.total), 1);
      evo.innerHTML = data.evolucao_7dias.map(e => {
        const pct = Math.round((e.total / max) * 100);
        return `
          <div class="evo-row">
            <span class="evo-dia">${e.dia.slice(5)}</span>
            <div class="evo-barra-bg">
              <div class="evo-barra" style="width:${pct}%"></div>
            </div>
            <span class="evo-num">${e.total}</span>
          </div>`;
      }).join("");
    }
  }
}

function setTexto(id, valor) {
  const el = document.getElementById(id);
  if (el) el.textContent = valor;
}

function escHtml(v) {
  return String(v).replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}
