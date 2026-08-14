import json


CONFIRMED_PRIME = "#008A7C"
UNRESOLVED_CANDIDATE = "#2457E6"
NEWLY_RESOLVED = "#D97706"
RESOLVED_COMPOSITE = "#E3E8EF"
NEUTRAL = "#FFFFFF"
INK = "#172033"
MUTED = "#667085"
BORDER = "#C7D0DD"


def build_kinetic_sieve_html(
    *,
    base_speed: float = 1.55,
    maximum_value: int = 2_000_000,
) -> str:
    """Build the self contained browser animation for Kinetic Sieve Lab."""

    if base_speed <= 0:
        raise ValueError("base_speed must be positive")

    if maximum_value < 100:
        raise ValueError("maximum_value must be at least 100")

    config = json.dumps(
        {
            "baseSpeed": base_speed,
            "maximumValue": maximum_value,
            "colors": {
                "confirmed": CONFIRMED_PRIME,
                "candidate": UNRESOLVED_CANDIDATE,
                "newlyResolved": NEWLY_RESOLVED,
                "resolved": RESOLVED_COMPOSITE,
                "neutral": NEUTRAL,
                "ink": INK,
                "muted": MUTED,
                "border": BORDER,
            },
        }
    )

    return f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<style>
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; background: transparent; color: {INK}; }}
    body {{ font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .shell {{
        width: 100%;
        border: 1px solid #D7DEE8;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.76);
        overflow: hidden;
    }}
    .top {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 1px;
        background: #E6EBF2;
        border-bottom: 1px solid #D7DEE8;
    }}
    .metric {{ background: #FFFFFF; padding: 12px 14px; min-height: 70px; }}
    .metric-label {{ color: #667085; font-size: 12px; margin-bottom: 5px; }}
    .metric-value {{ color: #172033; font-size: 21px; font-weight: 650; line-height: 1.1; }}
    .stage-wrap {{ position: relative; background: #FBFCFE; }}
    canvas {{ width: 100%; height: 500px; display: block; }}
    .toolbar {{
        min-height: 46px;
        padding: 8px 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        border-top: 1px solid #E6EBF2;
        background: #FFFFFF;
        color: #667085;
        font-size: 12px;
    }}
    .controls {{ display: flex; align-items: center; gap: 8px; }}
    button {{
        border: 1px solid #C7D0DD;
        border-radius: 7px;
        padding: 6px 10px;
        background: #FFFFFF;
        color: #344054;
        cursor: pointer;
        font: inherit;
    }}
    button:hover {{ background: #F8FAFC; }}
    button.active {{ border-color: #98A2B3; background: #F2F4F7; font-weight: 650; }}
    .legend {{ display: flex; gap: 14px; flex-wrap: wrap; align-items: center; }}
    .legend-item {{ display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }}
    .swatch {{ width: 10px; height: 10px; border-radius: 3px; border: 1px solid rgba(23,32,51,.14); }}
    @media (max-width: 850px) {{
        .top {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
        .toolbar {{ align-items: flex-start; flex-direction: column; }}
        canvas {{ height: 470px; }}
    }}
</style>
</head>
<body>
<div class="shell">
    <div class="top">
        <div class="metric"><div class="metric-label">Frontier</div><div id="frontierValue" class="metric-value">1</div></div>
        <div class="metric"><div class="metric-label">Latest confirmed prime</div><div id="latestPrime" class="metric-value">None yet</div></div>
        <div class="metric"><div class="metric-label">Confirmed primes discovered</div><div id="primeCount" class="metric-value">0</div></div>
        <div class="metric"><div class="metric-label">Latest shared meeting</div><div id="latestMeeting" class="metric-value">None yet</div></div>
    </div>
    <div class="stage-wrap"><canvas id="stage"></canvas></div>
    <div class="toolbar">
        <div class="legend">
            <span class="legend-item"><span class="swatch" style="background:{UNRESOLVED_CANDIDATE}"></span>Unresolved candidate</span>
            <span class="legend-item"><span class="swatch" style="background:{CONFIRMED_PRIME}"></span>Confirmed prime</span>
            <span class="legend-item"><span class="swatch" style="background:{NEWLY_RESOLVED}"></span>Newly resolved composite</span>
            <span class="legend-item"><span class="swatch" style="background:{RESOLVED_COMPOSITE}"></span>Resolved composite</span>
        </div>
        <div class="controls">
            <button id="pauseButton">Pause</button>
            <button class="speed" data-speed="0.5">0.5×</button>
            <button class="speed active" data-speed="1">1×</button>
            <button class="speed" data-speed="2">2×</button>
        </div>
    </div>
</div>
<script>
(() => {{
    const CONFIG = {config};
    const canvas = document.getElementById("stage");
    const ctx = canvas.getContext("2d");
    const colors = CONFIG.colors;

    const frontierValue = document.getElementById("frontierValue");
    const latestPrime = document.getElementById("latestPrime");
    const primeCount = document.getElementById("primeCount");
    const latestMeeting = document.getElementById("latestMeeting");
    const pauseButton = document.getElementById("pauseButton");
    const speedButtons = Array.from(document.querySelectorAll("button.speed"));

    let cssWidth = 1200;
    let cssHeight = 500;
    let dpr = Math.max(1, Math.min(window.devicePixelRatio || 1, 2));

    let running = true;
    let speedMultiplier = 1;
    let simPosition = 1.55;
    let processedThrough = 1;
    let latestConfirmedPrime = null;
    let primes = [];
    let resolved = new Map();
    let lastEvent = null;
    let lastTimestamp = performance.now();

    const CELL_SIZE = 44;
    const CELL_GAP = 7;
    const PITCH = CELL_SIZE + CELL_GAP;
    const LEFT_PAD = 30;
    const RIGHT_PAD = 30;
    const ROW_Y_RATIO = 0.72;
    const EVENT_GLOW_SPAN = 0.58;
    const CORE_TRACK_LIMIT = 113;
    const LARGE_PRIME_LOOKAHEAD = 9;
    const MEETING_HOLD_SPAN = 0.13;

    function resize() {{
        const rect = canvas.getBoundingClientRect();
        cssWidth = Math.max(320, rect.width);
        cssHeight = Math.max(420, rect.height);
        dpr = Math.max(1, Math.min(window.devicePixelRatio || 1, 2));
        canvas.width = Math.round(cssWidth * dpr);
        canvas.height = Math.round(cssHeight * dpr);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }}

    new ResizeObserver(resize).observe(canvas);
    resize();

    function roundedRect(x, y, w, h, r) {{
        const rr = Math.min(r, w / 2, h / 2);
        ctx.beginPath();
        ctx.moveTo(x + rr, y);
        ctx.arcTo(x + w, y, x + w, y + h, rr);
        ctx.arcTo(x + w, y + h, x, y + h, rr);
        ctx.arcTo(x, y + h, x, y, rr);
        ctx.arcTo(x, y, x + w, y, rr);
        ctx.closePath();
    }}

    function factorsFor(value) {{
        if (value < 2) return [];

        let remaining = value;
        const factors = [];

        for (const p of primes) {{
            if (p * p > remaining) break;
            if (remaining % p !== 0) continue;

            factors.push(p);
            while (remaining % p === 0) remaining /= p;
        }}

        if (remaining > 1 && factors.length > 0) factors.push(remaining);
        return factors;
    }}

    function processInteger(value) {{
        if (value < 2) return;

        const factors = factorsFor(value);

        if (factors.length === 0) {{
            primes.push(value);
            latestConfirmedPrime = value;
            resolved.set(value, {{
                status: "prime",
                first: null,
                factors: [],
                eventAt: value,
            }});
            lastEvent = {{ value, kind: "prime", factors: [], eventAt: value }};
        }} else {{
            const first = factors[0];
            resolved.set(value, {{
                status: "composite",
                first,
                factors,
                eventAt: value,
            }});

            lastEvent = {{
                value,
                kind: factors.length >= 2 ? "meeting" : "composite",
                factors,
                first,
                eventAt: value,
            }};
        }}

        processedThrough = value;
        frontierValue.textContent = value.toLocaleString();
        latestPrime.textContent = latestConfirmedPrime === null ? "None yet" : latestConfirmedPrime.toLocaleString();
        primeCount.textContent = primes.length.toLocaleString();

        if (lastEvent.kind === "meeting") {{
            latestMeeting.textContent = `${{lastEvent.factors.join(" · ")}} at ${{value.toLocaleString()}}`;
        }}
    }}

    function ensureProcessed() {{
        const target = Math.floor(simPosition + 1e-9);
        while (processedThrough < target) {{
            processInteger(processedThrough + 1);
        }}
    }}

    function windowGeometry() {{
        const count = Math.max(12, Math.floor((cssWidth - LEFT_PAD - RIGHT_PAD) / PITCH));
        const anchor = Math.max(7, Math.floor(count * 0.68));
        const smoothStart = Math.max(0, simPosition - anchor);
        const first = Math.floor(smoothStart);
        return {{ count, anchor, smoothStart, first }};
    }}

    function worldX(value, geometry) {{
        return LEFT_PAD + (value - geometry.smoothStart) * PITCH + CELL_SIZE / 2;
    }}

    function cellState(value) {{
        if (value < 2) return {{ status: "neutral" }};
        if (value > processedThrough) return {{ status: "candidate" }};
        return resolved.get(value) || {{ status: "candidate" }};
    }}

    function drawCell(value, geometry, rowY) {{
        const centerX = worldX(value, geometry);
        const x = centerX - CELL_SIZE / 2;
        const y = rowY - CELL_SIZE / 2;
        const state = cellState(value);

        let fill = colors.candidate;
        let textColor = "#FFFFFF";
        let borderColor = "rgba(23,32,51,.16)";

        if (state.status === "neutral") {{
            fill = colors.neutral;
            textColor = colors.ink;
            borderColor = colors.border;
        }} else if (state.status === "prime") {{
            fill = colors.confirmed;
            textColor = "#FFFFFF";
        }} else if (state.status === "composite") {{
            const age = simPosition - state.eventAt;
            fill = age <= EVENT_GLOW_SPAN ? colors.newlyResolved : colors.resolved;
            textColor = age <= EVENT_GLOW_SPAN ? "#FFFFFF" : colors.ink;
        }}

        roundedRect(x, y, CELL_SIZE, CELL_SIZE, 8);
        ctx.fillStyle = fill;
        ctx.fill();
        ctx.strokeStyle = borderColor;
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.fillStyle = textColor;
        ctx.font = "600 14px Inter, system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(value.toLocaleString(), centerX, rowY + 0.5);

        if (state.status === "prime" && value < simPosition - 0.15) {{
            ctx.strokeStyle = colors.confirmed;
            ctx.globalAlpha = 0.42;
            ctx.lineWidth = 2;
            roundedRect(x + 4, y + 4, CELL_SIZE - 8, CELL_SIZE - 8, 6);
            ctx.stroke();
            ctx.globalAlpha = 1;
        }}
    }}

    function shouldDrawPrime(prime) {{
        if (prime > simPosition + 1e-9) return false;
        if (prime <= CORE_TRACK_LIMIT) return true;

        const justBorn = simPosition - prime <= 0.9;
        if (justBorn) return true;

        const nextMultiple = Math.ceil((simPosition + 1e-9) / prime) * prime;
        return nextMultiple - simPosition <= LARGE_PRIME_LOOKAHEAD;
    }}

    function drawPrimeToken(prime, displayIndex, geometry, rowY) {{
        const phase = ((simPosition % prime) + prime) % prime / prime;
        const arc = Math.sin(Math.PI * phase);
        const amplitude = 72 + Math.min(220, displayIndex * 7.6);
        let x = worldX(simPosition, geometry);
        let y = rowY - amplitude * arc;

        if (
            lastEvent
            && lastEvent.kind === "meeting"
            && lastEvent.factors.includes(prime)
            && simPosition - lastEvent.eventAt >= 0
            && simPosition - lastEvent.eventAt <= MEETING_HOLD_SPAN
        ) {{
            x = worldX(lastEvent.value, geometry);
            y = rowY;
        }}

        const size = 30;
        const justBorn = Math.max(0, 1 - (simPosition - prime) / 0.65);
        const scale = 1 + 0.22 * justBorn;
        const drawSize = size * scale;

        ctx.save();
        ctx.shadowColor = `rgba(0,138,124,${{0.18 + 0.12 * arc}})`;
        ctx.shadowBlur = 9;
        roundedRect(x - drawSize / 2, y - drawSize / 2, drawSize, drawSize, 7);
        ctx.fillStyle = colors.confirmed;
        ctx.fill();
        ctx.shadowBlur = 0;
        ctx.strokeStyle = "rgba(255,255,255,.55)";
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.fillStyle = "#FFFFFF";
        ctx.font = "650 12px Inter, system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(prime.toString(), x, y + 0.5);
        ctx.restore();
    }}

    function drawFrontier(geometry, rowY) {{
        const x = worldX(simPosition, geometry);
        ctx.save();
        ctx.strokeStyle = "rgba(36,87,230,.30)";
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 5]);
        ctx.beginPath();
        ctx.moveTo(x, 42);
        ctx.lineTo(x, rowY + CELL_SIZE * 0.9);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = colors.muted;
        ctx.font = "600 11px Inter, system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("discovery frontier", x, 28);
        ctx.restore();
    }}

    function drawMeetingPulse(geometry, rowY) {{
        if (!lastEvent || lastEvent.kind !== "meeting") return;
        const age = simPosition - lastEvent.eventAt;
        if (age < 0 || age > 0.72) return;

        const x = worldX(lastEvent.value, geometry);
        if (x < -60 || x > cssWidth + 60) return;

        const progress = Math.min(1, age / 0.72);
        const radius = 26 + 28 * progress;

        ctx.save();
        ctx.globalAlpha = 0.72 * (1 - progress);
        ctx.strokeStyle = colors.confirmed;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(x, rowY, radius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();

        ctx.save();
        ctx.fillStyle = colors.ink;
        ctx.font = "650 13px Inter, system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(
            `${{lastEvent.factors.join(" · ")}} meet at ${{lastEvent.value.toLocaleString()}}`,
            x,
            Math.max(54, rowY - 255),
        );
        ctx.restore();
    }}

    function drawPrimeDiscovery(geometry, rowY) {{
        if (!lastEvent || lastEvent.kind !== "prime") return;
        const age = simPosition - lastEvent.eventAt;
        if (age < 0 || age > 0.8) return;

        const x = worldX(lastEvent.value, geometry);
        if (x < -60 || x > cssWidth + 60) return;

        const progress = Math.min(1, age / 0.8);
        ctx.save();
        ctx.globalAlpha = 1 - 0.7 * progress;
        ctx.fillStyle = colors.confirmed;
        ctx.font = "650 12px Inter, system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(
            `Prime ${{lastEvent.value.toLocaleString()}} confirmed`,
            x,
            rowY - 58 - 34 * progress,
        );
        ctx.restore();
    }}

    function drawStatusNote() {{
        if (!lastEvent) return;

        let text = "";
        if (lastEvent.kind === "prime") {{
            text = `${{lastEvent.value.toLocaleString()}} reached the frontier with no earlier prime trajectory landing on it.`;
        }} else if (lastEvent.kind === "meeting") {{
            text = `${{lastEvent.factors.join(", ")}} arrive together. ${{lastEvent.first}} remains the first eliminating prime.`;
        }} else {{
            text = `Prime ${{lastEvent.first}} resolves ${{lastEvent.value.toLocaleString()}} as composite.`;
        }}

        ctx.save();
        ctx.fillStyle = colors.muted;
        ctx.font = "12px Inter, system-ui, sans-serif";
        ctx.textAlign = "left";
        ctx.fillText(text, LEFT_PAD, cssHeight - 22);
        ctx.restore();
    }}

    function pruneResolved(geometry) {{
        const cutoff = geometry.first - 6;
        if (cutoff <= 0) return;

        for (const key of resolved.keys()) {{
            if (key >= cutoff) break;
            resolved.delete(key);
        }}
    }}

    function render() {{
        ctx.clearRect(0, 0, cssWidth, cssHeight);
        ctx.fillStyle = "#FBFCFE";
        ctx.fillRect(0, 0, cssWidth, cssHeight);

        const geometry = windowGeometry();
        const rowY = cssHeight * ROW_Y_RATIO;
        const first = Math.max(0, geometry.first - 1);
        const last = first + geometry.count + 3;

        drawFrontier(geometry, rowY);

        for (let value = first; value <= last; value += 1) {{
            drawCell(value, geometry, rowY);
        }}

        const displayPrimes = primes.filter(shouldDrawPrime);
        displayPrimes.forEach((prime, index) => drawPrimeToken(prime, index, geometry, rowY));

        drawMeetingPulse(geometry, rowY);
        drawPrimeDiscovery(geometry, rowY);
        drawStatusNote();
        pruneResolved(geometry);
    }}

    function frame(timestamp) {{
        const rawDelta = Math.max(0, (timestamp - lastTimestamp) / 1000);
        const delta = Math.min(rawDelta, 0.08);
        lastTimestamp = timestamp;

        if (running && simPosition < CONFIG.maximumValue) {{
            simPosition += CONFIG.baseSpeed * speedMultiplier * delta;
            simPosition = Math.min(simPosition, CONFIG.maximumValue);
            ensureProcessed();
        }}

        render();
        requestAnimationFrame(frame);
    }}

    pauseButton.addEventListener("click", () => {{
        running = !running;
        pauseButton.textContent = running ? "Pause" : "Resume";
    }});

    speedButtons.forEach((button) => {{
        button.addEventListener("click", () => {{
            speedMultiplier = Number(button.dataset.speed);
            speedButtons.forEach((item) => item.classList.remove("active"));
            button.classList.add("active");
        }});
    }});

    lastTimestamp = performance.now();
    requestAnimationFrame(frame);
}})();
</script>
</body>
</html>
"""
