const byId = id => document.getElementById(id);
const companies = ["Alder Works", "Birch Studio", "Cedar Group"];
const quarters = ["2026 Q1", "2026 Q2", "2026 Q3"];
for (const name of companies) byId("company").add(new Option(name, name));
for (const id of ["start", "end"]) {
  for (const q of quarters) byId(id).add(new Option(q, q));
}
byId("end").value = quarters.at(-1);

function showPeerOptions() {
  byId("peers").replaceChildren();
  for (const name of companies.filter(n => n !== byId("company").value)) {
    const label = document.createElement("label");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = name;
    input.checked = true;
    label.append(input, name);
    byId("peers").append(label);
  }
}

function settings() {
  return {
    company: byId("company").value,
    peers: [...document.querySelectorAll("#peers input:checked")].map(el => el.value),
    start: byId("start").value, end: byId("end").value,
    tier: document.querySelector("[name=tier]:checked").value,
  };
}

async function send(path) {
  const response = await fetch(path, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(settings()) });
  if (!response.ok) throw new Error("Select at least one peer and a valid quarter range.");
  return response;
}

function draw(report) {
  byId("period").textContent = report.start === report.end ? report.end : report.start + " – " + report.end;
  byId("focus-title").textContent = report.company;
  byId("finding").textContent = report.finding;
  byId("focus-key").textContent = report.company;
  byId("focus-pct").textContent = report.focus.pct.toFixed(1) + "%";
  byId("peer-pct").textContent = report.pool.pct.toFixed(1) + "%";
  byId("answers").textContent = report.focus.responses.toLocaleString();
  const chart = byId("chart");
  chart.replaceChildren();
  for (const item of report.topics) {
    const row = document.createElement("div");
    row.className = "row";
    const name = document.createElement("span");
    name.className = "topic";
    name.textContent = item.topic;
    const bars = document.createElement("div");
    bars.className = "bars";
    for (const [label, metric] of [[report.company, item.focus], ["Pooled peers", item.peers]]) {
      const measure = document.createElement("div");
      measure.className = "measure";
      const bar = document.createElement("i");
      bar.style.width = (metric.pct * .82) + "%";
      const text = document.createElement("span");
      text.textContent = metric.pct.toFixed(1) + "%";
      measure.setAttribute("aria-label", label + ": " + text.textContent);
      measure.append(bar, text);
      bars.append(measure);
    }
    const delta = document.createElement("span");
    delta.className = "gap";
    delta.textContent = (item.gap > 0 ? "+" : "") + item.gap.toFixed(1) + " pp";
    row.append(name, bars, delta);
    chart.append(row);
  }
}

let revision = 0;
async function refresh() {
  const version = ++revision;
  byId("download").disabled = true;
  try {
    const report = await (await send("/analysis")).json();
    if (version !== revision) return;
    draw(report);
    document.querySelector(".content").hidden = false;
    byId("download").disabled = false;
    byId("status").textContent = "";
  } catch (error) {
    if (version !== revision) return;
    document.querySelector(".content").hidden = true;
    byId("status").textContent = error.message;
  }
}
byId("settings").addEventListener("change", event => {
  if (event.target.id === "company") showPeerOptions();
  refresh();
});
byId("settings").addEventListener("submit", async event => {
  event.preventDefault();
  try {
    const file = await (await send("/presentation")).blob();
    const link = document.createElement("a");
    link.href = URL.createObjectURL(file);
    link.download = "employee-sentiment-analysis.pptx";
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    byId("status").textContent = "PowerPoint report generated.";
  } catch (error) {
    byId("status").textContent = error.message;
  }
});
showPeerOptions();
refresh();
