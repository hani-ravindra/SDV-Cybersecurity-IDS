let simulationTimer = null;
const maxEvents = 20;


async function checkStatus() {

    try {

        const response = await fetch("/api/status");
        const data = await response.json();

        document.getElementById("server-status").textContent =
            "SERVER ONLINE";

        document.getElementById("status-dot").style.background =
            "#69d18a";

        document.getElementById("system-status").textContent =
            "ONLINE";

        document.getElementById("feature-count").textContent =
            data.features;

        updateStats(data.stats);

    } catch (error) {

        document.getElementById("server-status").textContent =
            "SERVER OFFLINE";

        document.getElementById("status-dot").style.background =
            "#ff6573";

        document.getElementById("system-status").textContent =
            "OFFLINE";
    }
}


function updateStats(stats) {

    document.getElementById("total-count").textContent =
        stats.total;

    document.getElementById("normal-count").textContent =
        stats.normal;

    document.getElementById("attack-count").textContent =
        stats.attack;

    const rate =
        stats.total > 0
            ? (stats.attack / stats.total) * 100
            : 0;

    document.getElementById("attack-rate").textContent =
        rate.toFixed(1) + "%";
}


function updateDashboard(data) {

    document.getElementById("timestamp").textContent =
        data.timestamp;

    document.getElementById("scenario").textContent =
        data.scenario || "Normal / Random";

    document.getElementById("can-id").textContent =
        data.can_id;

    document.getElementById("payload").textContent =
        data.payload;

    document.getElementById("prediction").textContent =
        data.prediction;

    document.getElementById("confidence").textContent =
        data.confidence.toFixed(2) + "%";

    document.getElementById("latency").textContent =
        data.latency_ms.toFixed(3) + " ms";

    const predictionBox =
        document.getElementById("prediction-box");

    predictionBox.className =
        "prediction " +
        (data.prediction === "ATTACK"
            ? "attack"
            : "normal");

    updateStats(data.stats);

    if (data.prediction === "ATTACK") {
        showAttackAlert(data);
    } else {
        showNormalStatus(data);
    }

    addEvent(data);
}


function showAttackAlert(data) {

    const panel =
        document.getElementById("alert-panel");

    panel.classList.add("alert");

    document.getElementById("alert-title").textContent =
        "SECURITY ALERT — ATTACK DETECTED";

    const scenarioText =
        data.scenario
            ? `Scenario: ${data.scenario}. `
            : "";

    document.getElementById("alert-text").textContent =
        `${scenarioText}${data.can_id} classified as ATTACK with ${data.confidence.toFixed(2)}% confidence.`;
}


function showNormalStatus(data) {

    const panel =
        document.getElementById("alert-panel");

    panel.classList.remove("alert");

    document.getElementById("alert-title").textContent =
        "TRAFFIC NORMAL";

    document.getElementById("alert-text").textContent =
        "Latest CAN message was classified as normal.";
}


function addEvent(data) {

    const table =
        document.getElementById("event-table");

    const empty =
        table.querySelector(".empty");

    if (empty) {
        table.innerHTML = "";
    }

    const row =
        document.createElement("tr");

    const resultClass =
        data.prediction === "ATTACK"
            ? "result-attack"
            : "result-normal";

    row.innerHTML = `
        <td>${data.timestamp}</td>
        <td>${data.scenario || "Random"}</td>
        <td class="mono">${data.can_id}</td>
        <td class="mono">${data.payload}</td>
        <td class="${resultClass}">${data.prediction}</td>
        <td>${data.confidence.toFixed(2)}%</td>
        <td>${data.latency_ms.toFixed(3)} ms</td>
    `;

    table.prepend(row);

    while (table.children.length > maxEvents) {
        table.removeChild(table.lastChild);
    }
}


async function testScenario(scenario) {

    stopSimulation();

    try {

        document.getElementById("alert-title").textContent =
            `TESTING ${scenario}`;

        document.getElementById("alert-text").textContent =
            "Replaying one labeled CAN message through the IDS...";

        const encodedScenario =
            encodeURIComponent(scenario);

        const response =
            await fetch(
                `/api/scenario/${encodedScenario}`
            );

        const data =
            await response.json();

        if (!data.success) {
            throw new Error(data.error);
        }

        updateDashboard(data);

    } catch (error) {

        console.error(error);

        document.getElementById("alert-title").textContent =
            "SCENARIO TEST ERROR";

        document.getElementById("alert-text").textContent =
            error.message;
    }
}


async function simulateOne() {

    try {

        const response =
            await fetch("/api/simulate");

        const data =
            await response.json();

        if (data.success) {
            updateDashboard(data);
        }

    } catch (error) {

        console.error(
            "Simulation error:",
            error
        );

        stopSimulation();
    }
}


function startSimulation() {

    if (simulationTimer !== null) {
        return;
    }

    document.getElementById("start-btn").textContent =
        "Running...";

    document.getElementById("start-btn").disabled =
        true;

    simulateOne();

    simulationTimer =
        setInterval(
            simulateOne,
            1000
        );
}


function stopSimulation() {

    if (simulationTimer !== null) {

        clearInterval(
            simulationTimer
        );

        simulationTimer = null;
    }

    document.getElementById("start-btn").textContent =
        "Start Simulation";

    document.getElementById("start-btn").disabled =
        false;
}


async function resetDashboard() {

    stopSimulation();

    await fetch(
        "/api/reset",
        {
            method: "POST"
        }
    );

    updateStats({
        total: 0,
        normal: 0,
        attack: 0
    });

    document.getElementById("timestamp").textContent =
        "--:--:--";

    document.getElementById("scenario").textContent =
        "---";

    document.getElementById("can-id").textContent =
        "---";

    document.getElementById("payload").textContent =
        "-- -- -- -- -- -- -- --";

    document.getElementById("prediction").textContent =
        "WAITING";

    document.getElementById("confidence").textContent =
        "--";

    document.getElementById("latency").textContent =
        "--";

    document.getElementById("prediction-box").className =
        "prediction normal";

    document.getElementById("event-table").innerHTML = `
        <tr>
            <td colspan="7" class="empty">
                No CAN messages detected yet.
            </td>
        </tr>
    `;

    const panel =
        document.getElementById("alert-panel");

    panel.classList.remove("alert");

    document.getElementById("alert-title").textContent =
        "SYSTEM READY";

    document.getElementById("alert-text").textContent =
        "Select an attack scenario or start simulated CAN traffic.";
}


checkStatus();
