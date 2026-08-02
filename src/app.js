/* Passeport de l'Explorateur du Québec — app.js
   Single-page app: fetches data/*.json, renders timeline + detail pages,
   persists progress (validation, activities, photo souvenir) in localStorage. */

(() => {
  "use strict";

  const STOP_FILES = [
    "etape-1-montreal.json",
    "etape-2-mauricie.json",
    "etape-3-lac-saint-jean.json",
    "etape-4-fjord-saguenay.json",
    "etape-5-tadoussac.json",
    "etape-6-quebec.json"
  ];

  const PROGRESS_KEY = "passeport-quebec-progress-v1";
  const app = document.getElementById("app");

  let STOPS = [];

  // ---------- Persistence ----------
  function getProgress() {
    try {
      return JSON.parse(localStorage.getItem(PROGRESS_KEY)) || {};
    } catch (e) {
      return {};
    }
  }

  function saveProgress(p) {
    try {
      localStorage.setItem(PROGRESS_KEY, JSON.stringify(p));
    } catch (e) {
      console.warn("Impossible de sauvegarder la progression (stockage plein ?)", e);
    }
  }

  function getStopState(id) {
    const p = getProgress();
    if (!p[id]) p[id] = { valide: false, activites: {}, photo: null };
    return p[id];
  }

  function updateStopState(id, mutator) {
    const p = getProgress();
    if (!p[id]) p[id] = { valide: false, activites: {}, photo: null };
    mutator(p[id]);
    saveProgress(p);
  }

  // ---------- Data loading ----------
  async function loadAllData() {
    const results = await Promise.all(
      STOP_FILES.map((f) => fetch(`../data/${f}`).then((r) => r.json()))
    );
    return results.sort((a, b) => a.ordre - b.ordre);
  }

  // ---------- Helpers ----------
  function esc(str) {
    return String(str).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  function stopIndex(id) {
    return STOPS.findIndex((s) => s.id === id);
  }

  // ---------- Router ----------
  function currentRoute() {
    const hash = location.hash.replace(/^#\/?/, "");
    if (!hash) return { view: "home" };
    if (hash === "recap") return { view: "recap" };
    const m = hash.match(/^etape\/(.+)$/);
    if (m) return { view: "detail", id: m[1] };
    return { view: "home" };
  }

  function render() {
    const route = currentRoute();
    window.scrollTo(0, 0);
    if (route.view === "home") renderHome();
    else if (route.view === "recap") renderRecap();
    else if (route.view === "detail") renderDetail(route.id);
    else renderHome();
  }

  window.addEventListener("hashchange", render);

  // ---------- Views ----------
  function progressCount() {
    const p = getProgress();
    return STOPS.filter((s) => p[s.id] && p[s.id].valide).length;
  }

  function renderHome() {
    const done = progressCount();
    app.innerHTML = `
      <div class="screen">
        <div class="topbar">
          <div class="topbar-title">🧭 Passeport de l'Explorateur</div>
          <div class="progress-pill">${done} / ${STOPS.length} 🏅</div>
        </div>
        <div class="cover">
          <div class="flag-row">🇫🇷 ⇄ 🇨🇦</div>
          <h1>Passeport de l'Explorateur du Québec</h1>
          <p class="cover-sub">Suis le fil rouge de la Nouvelle-France, de Montréal jusqu'à Québec. Tamponne chaque étape que tu termines !</p>
        </div>
        <div class="timeline">
          ${STOPS.map((s) => stopRowHtml(s)).join("")}
        </div>
        <a class="stop-nav" href="#/recap" style="margin:0 16px 8px; display:flex;">
          <button style="width:100%;">🏅 Voir mon carnet de badges</button>
        </a>
        <p class="footer-note">Fonctionne 100% hors connexion, une fois installé sur l'écran d'accueil.</p>
      </div>
    `;
  }

  function stopRowHtml(s) {
    const st = getStopState(s.id);
    return `
      <a class="stop ${st.valide ? "done" : ""}" href="#/etape/${s.id}" style="text-decoration:none; color:inherit;">
        <div class="stop-badge" style="border-color:${st.valide ? "" : s.badge.couleur}">
          <span>${s.badge.emoji}</span>
          <span class="check">✓</span>
        </div>
        <div class="stop-card">
          <div class="stop-order">Étape ${s.ordre}</div>
          <h2>${esc(s.ville)}</h2>
          <div class="stop-dates">${formatDates(s.dates)}</div>
          <div class="stop-accroche">${esc(s.accroche)}</div>
        </div>
      </a>
    `;
  }

  function formatDates(d) {
    const fmt = (iso) => {
      const [y, m, day] = iso.split("-");
      const mois = ["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."];
      return `${parseInt(day,10)} ${mois[parseInt(m,10)-1]}`;
    };
    return `${fmt(d.debut)} → ${fmt(d.fin)} · ${d.duree}`;
  }

  function renderRecap() {
    const p = getProgress();
    const done = progressCount();
    app.innerHTML = `
      <div class="screen">
        <div class="topbar">
          <a class="back-btn" href="#/">←</a>
          <div class="topbar-title">🏅 Mon carnet de badges</div>
        </div>
        <div class="cover">
          <h1>${done === STOPS.length ? "Explorateur du Québec confirmé !" : `${done} badge${done>1?"s":""} sur ${STOPS.length}`}</h1>
          <p class="cover-sub">${done === STOPS.length ? "Bravo, tu as complété tout le passeport ! 🎉" : "Continue ton voyage pour débloquer tous les badges."}</p>
        </div>
        <div class="recap-grid">
          ${STOPS.map((s) => {
            const st = p[s.id];
            const isDone = !!(st && st.valide);
            return `<a href="#/etape/${s.id}" style="text-decoration:none;">
              <div class="recap-badge ${isDone ? "done" : ""}" style="border-color:${isDone ? "" : s.badge.couleur}">${s.badge.emoji}</div>
            </a>`;
          }).join("")}
        </div>
      </div>
    `;
  }

  function renderDetail(id) {
    const s = STOPS.find((x) => x.id === id);
    if (!s) { location.hash = "#/"; return; }
    const st = getStopState(id);
    const idx = stopIndex(id);
    const prev = STOPS[idx - 1];
    const next = STOPS[idx + 1];

    app.innerHTML = `
      <div class="screen" style="--badge-color:${s.badge.couleur}">
        <div class="topbar">
          <a class="back-btn" href="#/">←</a>
          <div class="topbar-title">${esc(s.ville)}</div>
        </div>

        <div class="hero">
          <div class="hero-badge">${s.badge.emoji}</div>
          <h1>${esc(s.ville)}</h1>
          <div class="hero-sub">${esc(s.accroche)}</div>
          <div class="hero-dates">${formatDates(s.dates)}</div>
          <div class="validate-row">
            <button class="validate-btn ${st.valide ? "done" : ""}" id="validateBtn">
              <span class="stamp">${st.valide ? "✅" : "⬜"}</span>
              <span>${st.valide ? "Étape validée !" : "Marquer comme validée"}</span>
            </button>
          </div>
        </div>

        <section class="card-section">
          <h2>🗺️ Ta carte carnet</h2>
          <div class="carnet-grid">
            <div class="carnet-box"><b>Où on est</b>${esc(s.carnet.ouOnEst)}</div>
            <div class="carnet-box"><b>À quoi ça ressemble</b>${esc(s.carnet.aQuoiCaRessemble)}</div>
          </div>
        </section>

        <section class="card-section">
          <h2>📖 Histoire &amp; culture</h2>
          ${s.histoire.map((h) => `
            <div class="anecdote">
              <h3>${esc(h.titre)}</h3>
              <p>${esc(h.texte)}</p>
            </div>
          `).join("")}
          <div class="anecdote">
            <h3>${esc(s.culture.titre)}</h3>
            <p>${esc(s.culture.texte)}</p>
          </div>
        </section>

        <section class="card-section">
          <h2>🍴 Spécialité locale : ${esc(s.specialite.nom)}</h2>
          <p>${esc(s.specialite.texte)}</p>
          <ul class="specialite-list">
            ${s.specialite.aGouter.map((it) => `<li>${esc(it)}</li>`).join("")}
          </ul>
        </section>

        <section class="card-section">
          <h2>📍 À ne pas manquer</h2>
          <div class="poi-grid">
            ${s.pointsInteret.map((poi) => `
              <div class="poi-card">
                <div class="poi-emoji">${poi.emoji}</div>
                <h3>${esc(poi.nom)}</h3>
                <p>${esc(poi.texte)}</p>
              </div>
            `).join("")}
          </div>
        </section>

        <div class="mot-quebecois">
          <div class="mot">${esc(s.motQuebecois.mot)}</div>
          <div class="signif">${esc(s.motQuebecois.signification)}</div>
          <div class="exemple">💬 ${esc(s.motQuebecois.exemple)}</div>
          <div class="clin">🇫🇷 ${esc(s.motQuebecois.clinDoeil)}</div>
        </div>

        <section class="card-section">
          <h2>🎮 À toi de jouer !</h2>
          ${s.activites.map((a, i) => renderActivity(a, i, st)).join("")}
        </section>

        <section class="card-section">
          <h2>📸 Photo souvenir</h2>
          <div class="photo-box" id="photoBox">
            ${st.photo ? `<img class="photo-preview" src="${st.photo}" alt="Photo souvenir">` : ""}
            <label class="photo-btn">
              <input type="file" accept="image/*" capture="environment" id="photoInput" style="display:none;">
              ${st.photo ? "🔄 Reprendre une photo" : "📷 Prendre une photo"}
            </label>
          </div>
        </section>

        <div class="fil-rouge">
          <div class="flags">🇫🇷⇄🇨🇦</div>
          <div>${esc(s.filRouge)}</div>
        </div>

        <div class="stop-nav">
          <button id="prevBtn" ${prev ? "" : "disabled"}>← ${prev ? esc(prev.ville) : ""}</button>
          <button id="nextBtn" ${next ? "" : "disabled"}>${next ? esc(next.ville) : ""} →</button>
        </div>
      </div>
    `;

    wireDetailHandlers(s, st, prev, next);
  }

  // ---------- Activity rendering ----------
  function renderActivity(a, i, st) {
    const state = st.activites[i] || {};
    let body = "";
    if (a.type === "chercheEtTrouve") body = renderChecklist(a, i, state);
    else if (a.type === "bingo") body = renderBingo(a, i, state);
    else if (a.type === "vraiFaux") body = renderVraiFaux(a, i, state);
    else if (a.type === "quiz") body = renderQuiz(a, i, state);
    else if (a.type === "enigme") body = renderEnigme(a, i, state);
    else if (a.type === "motsMeles") body = renderMotsMeles(a, i, state);
    else if (a.type === "dessine") body = renderDessine(a, i, state);
    return `
      <div class="activity" data-activity="${i}">
        <h2>${activityEmoji(a.type)} ${esc(a.titre)}</h2>
        <div class="consigne">${esc(a.consigne)}</div>
        ${body}
      </div>
    `;
  }

  function activityEmoji(type) {
    return { chercheEtTrouve: "🔍", bingo: "🎯", vraiFaux: "🤔", quiz: "❓", enigme: "🧩", motsMeles: "🔤", dessine: "🎨" }[type] || "🎲";
  }

  function renderChecklist(a, i, state) {
    const checked = state.checked || [];
    return `<ul class="checklist" data-kind="checklist">
      ${a.donnees.items.map((item, j) => `
        <li class="${checked.includes(j) ? "checked" : ""}" data-item="${j}">
          <input type="checkbox" ${checked.includes(j) ? "checked" : ""}>
          <span>${esc(item)}</span>
        </li>
      `).join("")}
    </ul>`;
  }

  function renderBingo(a, i, state) {
    const checked = state.checked || [];
    return `<div class="bingo-grid" data-kind="bingo">
      ${a.donnees.cases.map((c, j) => `
        <div class="bingo-cell ${checked.includes(j) ? "checked" : ""}" data-item="${j}">${esc(c)}</div>
      `).join("")}
    </div>`;
  }

  function renderVraiFaux(a, i, state) {
    const answers = state.answers || {};
    return a.donnees.questions.map((q, j) => {
      const sel = answers[j];
      const answered = sel !== undefined;
      return `
        <div class="vf-item" data-kind="vf" data-item="${j}">
          <p class="affirmation">${esc(q.affirmation)}</p>
          <div class="vf-buttons">
            <button data-val="true" class="${answered && sel === true ? "selected " + (q.reponse === true ? "correct" : "wrong") : ""}">Vrai</button>
            <button data-val="false" class="${answered && sel === false ? "selected " + (q.reponse === false ? "correct" : "wrong") : ""}">Faux</button>
          </div>
          <p class="vf-explication ${answered ? "show" : ""}">${esc(q.explication)}</p>
        </div>
      `;
    }).join("");
  }

  function renderQuiz(a, i, state) {
    const answers = state.answers || {};
    return a.donnees.questions.map((q, j) => {
      const sel = answers[j];
      const answered = sel !== undefined;
      return `
        <div class="quiz-item" data-kind="quiz" data-item="${j}">
          <p class="question">${esc(q.question)}</p>
          <div class="quiz-choices">
            ${q.choix.map((c, k) => `
              <button data-val="${k}" class="${answered && sel === k ? "selected " + (q.reponse === k ? "correct" : "wrong") : ""}">${esc(c)}</button>
            `).join("")}
          </div>
          <p class="quiz-explication ${answered ? "show" : ""}">${esc(q.explication)}</p>
        </div>
      `;
    }).join("");
  }

  function renderEnigme(a, i, state) {
    const revealed = !!state.revealed;
    return `
      <div class="enigme-box" data-kind="enigme">
        <p class="enigme-indice">💡 Indice : ${esc(a.donnees.indice)}</p>
        <button class="reveal-btn" data-revealed="${revealed}">${revealed ? "Masquer la réponse" : "Voir la réponse"}</button>
        <p class="enigme-reponse ${revealed ? "show" : ""}">${esc(a.donnees.reponse)}</p>
      </div>
    `;
  }

  function renderMotsMeles(a, i, state) {
    const found = state.found || [];
    const grid = a.donnees.grille;
    const cols = grid[0].length;
    const highlighted = state.highlighted || [];
    return `
      <div data-kind="motsmeles">
        <div class="motsmeles-grid" style="grid-template-columns: repeat(${cols}, 1fr);">
          ${grid.map((row, r) => row.split("").map((ch, c) => {
            const key = `${r}-${c}`;
            return `<div class="cell" data-key="${key}" style="${highlighted.includes(key) ? "background:var(--accent);color:#fff;" : ""}">${ch}</div>`;
          }).join("")).join("")}
        </div>
        <div class="motsmeles-words">
          ${a.donnees.mots.map((w, j) => `<span data-word="${j}" class="${found.includes(j) ? "found" : ""}">${esc(w)}</span>`).join("")}
        </div>
      </div>
    `;
  }

  function renderDessine(a, i, state) {
    return `
      <div data-kind="dessine">
        <canvas class="draw-canvas" width="640" height="480"></canvas>
        <div class="draw-tools">
          <input type="color" value="#2E86AB">
          <button data-tool="clear">🗑️ Effacer</button>
        </div>
      </div>
    `;
  }

  // ---------- Wiring ----------
  function wireDetailHandlers(s, st, prev, next) {
    const validateBtn = document.getElementById("validateBtn");
    validateBtn.addEventListener("click", () => {
      updateStopState(s.id, (state) => { state.valide = !state.valide; });
      renderDetail(s.id);
    });

    if (prev) document.getElementById("prevBtn").addEventListener("click", () => { location.hash = `#/etape/${prev.id}`; });
    if (next) document.getElementById("nextBtn").addEventListener("click", () => { location.hash = `#/etape/${next.id}`; });

    // Checklist / bingo
    app.querySelectorAll('[data-kind="checklist"] li, [data-kind="bingo"] .bingo-cell').forEach((el) => {
      el.addEventListener("click", () => {
        const activityEl = el.closest(".activity");
        const ai = parseInt(activityEl.dataset.activity, 10);
        const item = parseInt(el.dataset.item, 10);
        updateStopState(s.id, (state) => {
          if (!state.activites[ai]) state.activites[ai] = {};
          const arr = state.activites[ai].checked || [];
          const pos = arr.indexOf(item);
          if (pos === -1) arr.push(item); else arr.splice(pos, 1);
          state.activites[ai].checked = arr;
        });
        renderDetail(s.id);
      });
    });

    // Vrai/Faux
    app.querySelectorAll('[data-kind="vf"] .vf-buttons button').forEach((btn) => {
      btn.addEventListener("click", () => {
        const item = parseInt(btn.closest(".vf-item").dataset.item, 10);
        const ai = parseInt(btn.closest(".activity").dataset.activity, 10);
        const val = btn.dataset.val === "true";
        updateStopState(s.id, (state) => {
          if (!state.activites[ai]) state.activites[ai] = {};
          if (!state.activites[ai].answers) state.activites[ai].answers = {};
          state.activites[ai].answers[item] = val;
        });
        renderDetail(s.id);
      });
    });

    // Quiz
    app.querySelectorAll('[data-kind="quiz"] .quiz-choices button').forEach((btn) => {
      btn.addEventListener("click", () => {
        const item = parseInt(btn.closest(".quiz-item").dataset.item, 10);
        const ai = parseInt(btn.closest(".activity").dataset.activity, 10);
        const val = parseInt(btn.dataset.val, 10);
        updateStopState(s.id, (state) => {
          if (!state.activites[ai]) state.activites[ai] = {};
          if (!state.activites[ai].answers) state.activites[ai].answers = {};
          state.activites[ai].answers[item] = val;
        });
        renderDetail(s.id);
      });
    });

    // Énigme
    app.querySelectorAll('[data-kind="enigme"] .reveal-btn').forEach((btn) => {
      btn.addEventListener("click", () => {
        const ai = parseInt(btn.closest(".activity").dataset.activity, 10);
        updateStopState(s.id, (state) => {
          if (!state.activites[ai]) state.activites[ai] = {};
          state.activites[ai].revealed = !state.activites[ai].revealed;
        });
        renderDetail(s.id);
      });
    });

    // Mots mêlés — tap letters to trace, tap word chip to mark found
    app.querySelectorAll('[data-kind="motsmeles"] .cell').forEach((cell) => {
      cell.addEventListener("click", () => {
        const ai = parseInt(cell.closest(".activity").dataset.activity, 10);
        const key = cell.dataset.key;
        updateStopState(s.id, (state) => {
          if (!state.activites[ai]) state.activites[ai] = {};
          const arr = state.activites[ai].highlighted || [];
          const pos = arr.indexOf(key);
          if (pos === -1) arr.push(key); else arr.splice(pos, 1);
          state.activites[ai].highlighted = arr;
        });
        renderDetail(s.id);
      });
    });
    app.querySelectorAll('[data-kind="motsmeles"] .motsmeles-words span').forEach((chip) => {
      chip.addEventListener("click", () => {
        const ai = parseInt(chip.closest(".activity").dataset.activity, 10);
        const w = parseInt(chip.dataset.word, 10);
        updateStopState(s.id, (state) => {
          if (!state.activites[ai]) state.activites[ai] = {};
          const arr = state.activites[ai].found || [];
          const pos = arr.indexOf(w);
          if (pos === -1) arr.push(w); else arr.splice(pos, 1);
          state.activites[ai].found = arr;
        });
        renderDetail(s.id);
      });
    });

    // Dessine — canvas drawing
    app.querySelectorAll('[data-kind="dessine"]').forEach((wrap) => {
      const ai = parseInt(wrap.closest(".activity").dataset.activity, 10);
      const canvas = wrap.querySelector("canvas");
      const colorInput = wrap.querySelector('input[type="color"]');
      const clearBtn = wrap.querySelector('[data-tool="clear"]');
      const ctx = canvas.getContext("2d");
      let drawing = false;
      let last = null;

      const saved = st.activites[ai] && st.activites[ai].drawing;
      if (saved) {
        const img = new Image();
        img.onload = () => ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        img.src = saved;
      }

      function pos(e) {
        const rect = canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left) * (canvas.width / rect.width);
        const y = (e.clientY - rect.top) * (canvas.height / rect.height);
        return { x, y };
      }

      function save() {
        const dataUrl = canvas.toDataURL("image/png");
        updateStopState(s.id, (state) => {
          if (!state.activites[ai]) state.activites[ai] = {};
          state.activites[ai].drawing = dataUrl;
        });
      }

      canvas.addEventListener("pointerdown", (e) => {
        drawing = true;
        last = pos(e);
        canvas.setPointerCapture(e.pointerId);
      });
      canvas.addEventListener("pointermove", (e) => {
        if (!drawing) return;
        const p = pos(e);
        ctx.strokeStyle = colorInput.value;
        ctx.lineWidth = 5;
        ctx.lineCap = "round";
        ctx.beginPath();
        ctx.moveTo(last.x, last.y);
        ctx.lineTo(p.x, p.y);
        ctx.stroke();
        last = p;
      });
      ["pointerup", "pointerleave", "pointercancel"].forEach((ev) => {
        canvas.addEventListener(ev, () => { if (drawing) { drawing = false; save(); } });
      });
      clearBtn.addEventListener("click", () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        save();
      });
    });

    // Photo souvenir
    const photoInput = document.getElementById("photoInput");
    if (photoInput) {
      photoInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => {
          const img = new Image();
          img.onload = () => {
            const maxW = 800;
            const scale = Math.min(1, maxW / img.width);
            const c = document.createElement("canvas");
            c.width = img.width * scale;
            c.height = img.height * scale;
            const cx = c.getContext("2d");
            cx.drawImage(img, 0, 0, c.width, c.height);
            const dataUrl = c.toDataURL("image/jpeg", 0.8);
            updateStopState(s.id, (state) => { state.photo = dataUrl; });
            renderDetail(s.id);
          };
          img.src = reader.result;
        };
        reader.readAsDataURL(file);
      });
    }
  }

  // ---------- Boot ----------
  async function boot() {
    app.innerHTML = `<div class="screen"><div class="cover"><h1>🧭 Chargement du passeport…</h1></div></div>`;
    try {
      STOPS = await loadAllData();
      render();
    } catch (e) {
      app.innerHTML = `<div class="screen"><div class="cover"><h1>😕 Oups</h1><p class="cover-sub">Impossible de charger le passeport. Vérifie ta connexion la première fois que tu ouvres l'appli.</p></div></div>`;
      console.error(e);
    }
  }

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("service-worker.js").catch((e) => console.warn("SW registration failed", e));
    });
  }

  boot();
})();
