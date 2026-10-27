const $ = (id) => document.getElementById(id);

let monitoring = false;
let timer = null;
let requestInProgress = false;
let events = [];

function setMessage(message) {
    $("action-message").textContent = message;
}

function updateStats(stats) {
    $("total-count").textContent = stats.total ?? 0;
    $("attack-count").textContent = stats.attack ?? 0;
}


function setSecurityStatus(status) {
    const heading = $("security-status");
    const description = $("security-description");
    const car = document.querySelector(".car-art");

    heading.classList.remove("danger", "warning", "safe");

    if (car) {
        car.classList.remove("car-safe", "car-alert", "car-inactive");
    }

    if (!monitoring) {
        heading.textContent = "Monitoring Not Active";
        heading.classList.add("warning");

        description.textContent =
            "Start monitoring to analyse recorded vehicle messages.";

        $("network-status").textContent = "Monitoring inactive";
        $("network-status").className = "badge neutral";
        $("monitor-state").textContent = "Monitoring stopped";

        if (car) car.classList.add("car-inactive");
        return;
    }

    if (status === "ATTACK") {
        heading.textContent = "Suspicious Activity Detected";
        heading.classList.add("danger");

        description.textContent =
            "The model flagged the latest recorded message as suspicious. Review the security event history.";

        $("network-status").textContent = "Suspicious activity";
        $("network-status").className = "badge alert";
        $("monitor-state").textContent = "Monitoring recorded messages";

        if (car) car.classList.add("car-alert");

    } else if (status === "NORMAL") {
        heading.textContent = "Latest Message Normal";
        heading.classList.add("safe");

        description.textContent =
            "The latest recorded message was classified as normal. This does not guarantee that all vehicle messages are safe.";

        $("network-status").textContent = "Latest message normal";
        $("network-status").className = "badge";
        $("monitor-state").textContent = "Monitoring recorded messages";

        if (car) car.classList.add("car-safe");
    }
}

function updateSystemCards(status) {
    const text = status === "ATTACK"
        ? "Suspicious message"
        : "Normal message";

    ["engine-status", "braking-status", "transmission-status"].forEach((id) => {
        $(id).textContent = text;
        $(id).className = status === "ATTACK" ? "badge alert" : "badge";
    });
}

function addEvent(data) {
    events.unshift(data);
    events = events.slice(0, 30);
    renderEvents();
}

function renderEvents() {
    const list = $("event-list");
    list.replaceChildren();

    if (events.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 4;
        cell.className = "empty-state";
        cell.textContent =
            "No messages shown. Start monitoring to begin.";

        row.appendChild(cell);
        list.appendChild(row);
        return;
    }

    events.forEach((event) => {
        const row = document.createElement("tr");

        const time = document.createElement("td");
        time.textContent = event.timestamp || "--:--:--";

        const message = document.createElement("td");
        message.textContent = event.prediction === "ATTACK"
            ? "Suspicious network activity"
            : "Normal message detected";

        const result = document.createElement("td");
        result.textContent = event.prediction === "ATTACK"
            ? "SUSPICIOUS"
            : "NORMAL";
        result.className = event.prediction === "ATTACK"
            ? "result-attack"
            : "result-normal";

        const details = document.createElement("td");
        details.textContent =
            `${event.can_id || ""} · ${event.latency_ms ?? "—"} ms`;

        row.append(time, message, result, details);
        list.appendChild(row);
    });
}

async function processNextMessage() {
    if (!monitoring || requestInProgress) return;

    requestInProgress = true;

    try {
        const response = await fetch("/api/simulate");
        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Could not process a message.");
        }

        updateStats(data.stats);
        setSecurityStatus(data.prediction);
        updateSystemCards(data.prediction);

        $("latency").textContent =
            Number(data.latency_ms).toFixed(2);

        addEvent(data);

        if (data.prediction === "ATTACK") {
            setMessage(
                "Warning: the model flagged a recorded CAN message. Review the event."
            );
        } else {
            setMessage("Recorded message processed successfully.");
        }
    } catch (error) {
        setMessage(`Monitoring error: ${error.message}`);
        stopMonitoring();
    } finally {
        requestInProgress = false;
    }
}

function startMonitoring() {
    if (monitoring) return;

    monitoring = true;
    $("start-btn").disabled = true;
    $("stop-btn").disabled = false;
    $("mode-badge").textContent = "Monitoring";
    $("monitor-state").textContent = "Replaying recorded messages";
    setMessage("Monitoring started in recorded-data demo mode.");

    processNextMessage();
    timer = setInterval(processNextMessage, 1500);
}

function stopMonitoring() {
    monitoring = false;

    if (timer !== null) {
        clearInterval(timer);
        timer = null;
    }

    $("start-btn").disabled = false;
    $("stop-btn").disabled = true;
    $("mode-badge").textContent = "Stopped";
    $("monitor-state").textContent = "Monitoring stopped";

    // Clear stale security indicators when monitoring stops.
    $("security-status").textContent = "Monitoring Not Active";
    $("security-status").classList.remove("danger");
    $("security-status").classList.add("warning");

    $("security-description").textContent =
        "Start monitoring to analyse recorded vehicle messages.";

    $("network-status").textContent = "Monitoring inactive";
    $("network-status").className = "badge neutral";

    [
        "engine-status",
        "braking-status",
        "transmission-status"
    ].forEach((id) => {
        $(id).textContent = "Awaiting data";
        $(id).className = "badge neutral";
    });
}

async function resetMonitoring() {
    stopMonitoring();

    try {
        const response = await fetch("/api/reset", {
            method: "POST"
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Could not reset statistics.");
        }

        updateStats(data.stats);
        events = [];
        renderEvents();

        $("latency").textContent = "—";
        $("security-status").textContent = "Ready to monitor";
        $("security-status").classList.remove("danger", "warning");
        $("security-description").textContent =
            "Start monitoring to analyse recorded vehicle messages.";

        ["engine-status", "braking-status", "transmission-status",
         "network-status"].forEach((id) => {
            $(id).textContent = "Awaiting data";
            $(id).className = "badge neutral";
        });

        setMessage("Dashboard statistics reset. Recorded prediction logs are retained.");
    } catch (error) {
        setMessage(`Reset error: ${error.message}`);
    }
}

$("start-btn").addEventListener("click", startMonitoring);
$("stop-btn").addEventListener("click", () => {
    stopMonitoring();
    setSecurityStatus(null);
    setMessage("Monitoring stopped. You can resume when ready.");
});
$("reset-btn").addEventListener("click", resetMonitoring);

$("clear-events-btn").addEventListener("click", () => {
    events = [];
    renderEvents();
});

fetch("/api/status")
    .then((response) => response.json())
    .then((data) => updateStats(data.stats))
    .catch(() => setMessage("Unable to connect to the Flask backend."));