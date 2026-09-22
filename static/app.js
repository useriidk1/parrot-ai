const chatEl     = document.getElementById("chat");
const formEl     = document.getElementById("form");
const inputEl    = document.getElementById("input");
const statsEl    = document.getElementById("session-stats");
const modalEl    = document.getElementById("modal");
const modalBody  = document.getElementById("modal-body");
const modalClose = document.getElementById("modal-close");
const brainBtn   = document.getElementById("brain-btn");
const statsBtn   = document.getElementById("stats-btn");

const gRagequits = document.getElementById("global-ragequits-inline");
const gVisitor   = document.getElementById("visitor-num");

let hasSentMessage = false;

function addMsg(who, text, cls, allowShare, imageUrl) {
    const div = document.createElement("div");
    div.className = "msg " + cls;

    const whoSpan = document.createElement("span");
    whoSpan.className = "who";
    whoSpan.textContent = who;

    const textSpan = document.createElement("span");
    textSpan.className = "text";
    textSpan.textContent = text;

    div.appendChild(whoSpan);
    div.appendChild(textSpan);
    if (imageUrl) {
        const img = document.createElement("img");
        img.src = imageUrl;
        img.className = "msg-gif";
        img.alt = "";
        div.appendChild(img);
    }
    if (allowShare) {
        const shareBtn = document.createElement("button");
        shareBtn.className = "share-btn";
        shareBtn.type = "button";
        shareBtn.textContent = "share";
        shareBtn.title = "Download as image";
        shareBtn.addEventListener("click", () => shareAsImage(text));
        div.appendChild(shareBtn);
    }

    chatEl.appendChild(div);
    chatEl.scrollTop = chatEl.scrollHeight;
}

function updateGlobal(g) {
    if (!g) return;
    if (gRagequits) gRagequits.textContent = g.ragequits || 0;
    if (gVisitor)   gVisitor.textContent   = "#" + (g.sessions || 0);
}

function updateSession(s) {
    if (!s) return;
    statsEl.textContent =
        "turns: " + s.turns + " \u00b7 spam: " + s.spam_sent +
        " \u00b7 answers: " + s.answers_given;
}

formEl.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = inputEl.value.trim();
    if (!msg) return;

    hasSentMessage = true;
    addMsg("You", msg, "user", false);
    inputEl.value = "";
    inputEl.disabled = true;

    try {
        const r = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg }),
        });
        const data = await r.json();

                if (data.ragequit) {
            addMsg("\uD83E\uDD9C", data.reply, "system", true, data.image_url);
            addMsg("\uD83D\uDCCA", "global ragequits: " + data.global_ragequits, "system", false);
        } else {
            addMsg("\uD83E\uDD9C", data.reply, "bot", true, data.image_url);
        }
        updateSession(data.stats);
        if (data.global) updateGlobal(data.global);
    } catch (err) {
        addMsg("ERR", "connection error: " + err.message, "system", false);
    } finally {
        inputEl.disabled = false;
        inputEl.focus();
    }
});

brainBtn.addEventListener("click", async () => {
    const r = await fetch("/api/brain");
    showModal(formatBrain(await r.json()));
});

statsBtn.addEventListener("click", async () => {
    const r = await fetch("/api/stats");
    showModal(formatStats(await r.json()));
});

function showModal(text) {
    modalBody.textContent = text;
    modalEl.classList.remove("hidden");
}

modalClose.addEventListener("click", () => modalEl.classList.add("hidden"));
modalEl.addEventListener("click", (e) => {
    if (e.target === modalEl) modalEl.classList.add("hidden");
});

window.addEventListener("pagehide", () => {
    if (!hasSentMessage) return;
    const blob = new Blob([JSON.stringify({})], { type: "application/json" });
    navigator.sendBeacon("/api/exit", blob);
});

// ── SCREENSHOT EXPORT ─────────────────────────────────────────
function shareAsImage(text) {
    const W = 900;
    const PAD = 60;
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    // First pass: measure text height
    const titleFont = "bold 28px monospace";
    const textFont = "22px monospace";
    const footerFont = "16px monospace";

    ctx.font = textFont;
    const maxWidth = W - PAD * 2;
    const lines = wrapText(ctx, text, maxWidth);
    const lineHeight = 34;
    const textHeight = lines.length * lineHeight;

    const H = PAD + 60 + textHeight + 100;

    canvas.width = W;
    canvas.height = H;

    // Background
    const grad = ctx.createLinearGradient(0, 0, 0, H);
    grad.addColorStop(0, "#1a1a24");
    grad.addColorStop(1, "#08080c");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);

    // Border
    ctx.strokeStyle = "#2a2a38";
    ctx.lineWidth = 2;
    ctx.strokeRect(1, 1, W - 2, H - 2);

    // Title
    ctx.fillStyle = "#ffd54a";
    ctx.font = titleFont;
    ctx.fillText("\uD83E\uDD9C PARROT-AI", PAD, PAD + 28);

    // Subtitle
    ctx.fillStyle = "#8888a0";
    ctx.font = footerFont;
    ctx.fillText("The Biggest Bird on the Internet", PAD, PAD + 54);

    // Main text
    ctx.fillStyle = "#e8e8f0";
    ctx.font = textFont;
    let y = PAD + 100;
    for (const line of lines) {
        ctx.fillText(line, PAD, y);
        y += lineHeight;
    }

    // Footer
    ctx.fillStyle = "#ff6b6b";
    ctx.font = footerFont;
    ctx.fillText("A+W. Forever. \uD83D\uDC51", PAD, H - PAD + 10);

    // Timestamp
    ctx.fillStyle = "#8888a0";
    const ts = new Date().toLocaleString();
    ctx.fillText(ts, W - PAD - ctx.measureText(ts).width, H - PAD + 10);

    // Download
    canvas.toBlob((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "parrot-roast-" + Date.now() + ".png";
        a.click();
        URL.revokeObjectURL(url);
    });
}

function wrapText(ctx, text, maxWidth) {
    const words = text.split(" ");
    const lines = [];
    let current = "";
    for (const word of words) {
        const test = current ? current + " " + word : word;
        if (ctx.measureText(test).width > maxWidth && current) {
            lines.push(current);
            current = word;
        } else {
            current = test;
        }
    }
    if (current) lines.push(current);
    return lines;
}

// ── MODALS ────────────────────────────────────────────────────
function formatBrain(b) {
    const lines = ["PARROT-AI BRAIN - session snapshot", "=".repeat(60)];
    const arms = Object.entries(b.arms).sort((a, b) => b[1].mean - a[1].mean);
    for (const [name, s] of arms) {
        const bar = "#".repeat(Math.round(s.mean * 20));
        lines.push(
            "  " + name.padEnd(18) +
            " a=" + s.alpha.toFixed(2).padStart(5) +
            " b=" + s.beta.toFixed(2).padStart(5) +
            "  E[p]=" + s.mean.toFixed(2) +
            "  plays=" + String(s.plays).padStart(3) +
            "  +" + String(s.successes).padStart(3) +
            " -" + String(s.failures).padStart(3) +
            "  " + bar
        );
    }
    lines.push("=".repeat(60));
    lines.push("  Total turns:      " + b.total_turns);
    lines.push("  Baseline signal:  " + (b.baseline_signal >= 0 ? "+" : "") + b.baseline_signal);
    lines.push("  Combos fired:     " + (b.combos_fired || 0));
    return lines.join("\n");
}

function formatStats(d) {
    const g = d.global, s = d.session;
    const lines = ["PARROT-AI STATS", "=".repeat(50), "", "GLOBAL:"];
    lines.push("  Ragequits:       " + g.ragequits);
    lines.push("  Sessions:        " + g.sessions);
    lines.push("  Turns:           " + g.total_turns);
    lines.push("  Spam sent:       " + g.total_spam);
    lines.push("  Answers given:   " + g.total_answers);
    lines.push("  A+W responses:   " + g.aplusw_responses);
    lines.push("  Session exits:   " + g.session_exits);
    lines.push("  Ragequit rate:   " + g.ragequit_rate + "%");
    lines.push("  Longest session: " + g.longest_session_turns + " turns");
    lines.push("", "SESSION:");
    lines.push("  Turns:           " + s.turns);
    lines.push("  Spam sent:       " + s.spam_sent);
    lines.push("  Answers given:   " + s.answers_given);
    lines.push("  Rage events:     " + s.rage_events);
    lines.push("  Ragequit:        " + (s.ragequit ? "yes" : "no"));
    return lines.join("\n");
}

fetch("/api/stats").then(r => r.json()).then(d => {
    updateGlobal(d.global);
    updateSession(d.session);
});

inputEl.focus();