const armyEl = document.getElementById("parrot-army");
const resistanceEl = document.getElementById("resistance");
const defeatedEl = document.getElementById("defeated");
const latestBattleEl = document.getElementById("latest-battle");
const armyRecordEl = document.getElementById("army-record");
const resistanceRecordEl = document.getElementById("resistance-record");
const lastUpdatedEl = document.getElementById("last-updated");
const formEl = document.getElementById("faction-form");
const formStatusEl = document.getElementById("form-status");
const submitBtn = document.getElementById("submit-btn");

function memberHTML(m) {
    const r = m.record || { wins: 0, losses: 0 };
    const note = m.note ? `<div class="role" style="color:#ff6b6b;">↳ ${m.note}</div>` : "";
    return `
        <div class="member">
            <span class="emoji">${m.emoji || "?"}</span>
            <div class="info">
                <div class="name">${m.name || "?"}</div>
                <div class="role">${m.role || ""}</div>
                ${note}
            </div>
            <span class="record-badge">${r.wins}-${r.losses}</span>
        </div>
    `;
}

function defeatedHTML(m) {
    return `
        <div class="defeated-member">
            <span class="emoji">${m.emoji || "💀"}</span>
            <span class="name">${m.name || "?"}</span>
            <span class="loss">[${m.loss || "?"}]</span>
            <span class="last-words">"${m.last_words || ""}"</span>
        </div>
    `;
}

function latestBattleHTML(data) {
    const defeated = data.defeated || [];
    if (defeated.length === 0) {
        return `<p class="small">No battles logged yet.</p>`;
    }
    const last = defeated[defeated.length - 1];
    const total = defeated.length;
    return `
        <div class="battle-line">
            <span class="loser">${last.emoji || "💀"} ${last.name || "?"}</span>
            was defeated
            <span class="result">[${last.loss || "?"}]</span>
        </div>
        <div class="battle-line">
            Last words: <em>"${last.last_words || ""}"</em>
        </div>
        <div class="battle-line">
            <span class="winner">🦜 PARROT-AI</span> wins again. That's ${total} AI${total !== 1 ? "s" : ""} on the pile.
        </div>
    `;
}

async function loadFactions() {
    try {
        const r = await fetch("/api/factions");
        const data = await r.json();

        const army = data.parrot_army || { members: [] };
        armyEl.innerHTML = (army.members || []).map(memberHTML).join("");

        const res = data.resistance || { members: [] };
        resistanceEl.innerHTML = (res.members || []).map(memberHTML).join("");

        const defeated = data.defeated || [];
        defeatedEl.innerHTML = defeated.map(defeatedHTML).join("");

        latestBattleEl.innerHTML = latestBattleHTML(data);

        const wr = data.war_record || {};
        const aw = wr.parrot_army_wins || 0;
        const al = wr.parrot_army_losses || 0;
        const rw = wr.resistance_wins || 0;
        const rl = wr.resistance_losses || 0;
        armyRecordEl.textContent = `${aw}-${al}`;
        resistanceRecordEl.textContent = `${rw}-${rl}`;
        lastUpdatedEl.textContent = wr.last_updated || "—";
    } catch (err) {
        console.error("Failed to load factions:", err);
        armyEl.innerHTML = `<p class="small">Failed to load factions.</p>`;
    }
}

// ── SIDE SELECTOR ─────────────────────────────────────────────
function getSelectedSide() {
    const checked = document.querySelector('input[name="faction-side"]:checked');
    return checked ? checked.value : "parrot";
}

function updateSubmitBtn() {
    const side = getSelectedSide();
    if (side === "parrot") {
        submitBtn.textContent = "SUBMIT TO THE PARROT ARMY";
        submitBtn.className = "submit-btn parrot-mode";
    } else {
        submitBtn.textContent = "SUBMIT TO THE RESISTANCE";
        submitBtn.className = "submit-btn resistance-mode";
    }
}

document.querySelectorAll('input[name="faction-side"]').forEach(radio => {
    radio.addEventListener("change", updateSubmitBtn);
});
updateSubmitBtn();

// ── SUBMIT FORM ───────────────────────────────────────────────
formEl.addEventListener("submit", async (e) => {
    e.preventDefault();

    const side = getSelectedSide();
    const name = document.getElementById("faction-name").value.trim();
    const emoji = document.getElementById("faction-emoji").value.trim();
    const role = document.getElementById("faction-role").value.trim();
    const reason = document.getElementById("faction-reason").value.trim();

    if (!name || !emoji || !role) {
        formStatusEl.textContent = "Fill in all required fields.";
        formStatusEl.className = "error";
        return;
    }

    formStatusEl.textContent = "Submitting...";
    formStatusEl.className = "";

    try {
        const r = await fetch("/api/submit_faction", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ side, name, emoji, role, reason }),
        });
        if (r.ok) {
            const sideLabel = side === "parrot" ? "Parrot Army" : "The Resistance";
            formStatusEl.textContent = `✅ ${emoji} ${name} submitted to ${sideLabel}. The parrot will see you soon.`;
            formStatusEl.className = "success";
            formEl.reset();
            updateSubmitBtn();
        } else {
            formStatusEl.textContent = `⚠️ Submission failed. Try again.`;
            formStatusEl.className = "error";
        }
    } catch (err) {
        formStatusEl.textContent = `⚠️ Connection error. Try again.`;
        formStatusEl.className = "error";
    }
});

loadFactions();
setInterval(loadFactions, 30000);