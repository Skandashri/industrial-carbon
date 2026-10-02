// ==========================================================================
// INDUSTRIAL CARBON FORECASTING - CLIENT SCRIPT
// UI/UX Enhancements, Form Handling, Live IoT Polling & Graph Lightbox
// ==========================================================================

document.addEventListener("DOMContentLoaded", function () {
    console.log("🌱 Industrial Carbon Forecasting UI Initialized");

    // ======================================================================
    // 1. ACTIVE NAVIGATION LINK HIGHLIGHTING
    // ======================================================================
    const currentPath = window.location.pathname.replace(/\/+$/, "") || "/";
    const navLinks = document.querySelectorAll("nav ul li a, .nav-menu a, nav a");

    navLinks.forEach(link => {
        const href = link.getAttribute("href");
        if (!href) return;

        const normalizedHref = href.replace(/\/+$/, "") || "/";

        const isMatch = (normalizedHref === currentPath) ||
            (currentPath.startsWith("/predict") && normalizedHref === "/predict") ||
            (currentPath === "/predict_result" && normalizedHref === "/predict") ||
            (currentPath === "/predict-again" && normalizedHref === "/predict");

        if (isMatch) {
            link.classList.add("active");
        }
    });

    // ======================================================================
    // 2. MOBILE NAVIGATION DRAWER TOGGLE
    // ======================================================================
    const navToggle = document.querySelector(".mobile-nav-toggle");
    const navMenu = document.querySelector("nav ul, .nav-menu");

    if (navToggle && navMenu) {
        navToggle.addEventListener("click", function (e) {
            e.stopPropagation();
            const isOpen = navMenu.classList.toggle("open");
            navToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
        });

        document.addEventListener("click", function (e) {
            if (!navMenu.contains(e.target) && !navToggle.contains(e.target)) {
                navMenu.classList.remove("open");
                navToggle.setAttribute("aria-expanded", "false");
            }
        });
    }

    // ======================================================================
    // 3. AUTO-SCROLL TO PREDICTION RESULT (IF PRESENT)
    // ======================================================================
    const resultElement = document.querySelector(".prediction-result");
    if (resultElement) {
        setTimeout(() => {
            resultElement.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        }, 120);
    }

    // ======================================================================
    // 4. PREDICTION FORM CLIENT VALIDATION (CORE PARAMETERS ONLY)
    // ======================================================================
    const form = document.querySelector("form.prediction-form, form");

    if (form) {
        form.addEventListener("submit", function (e) {
            const energyEl = document.querySelector("[name='energy']");
            const prodEl = document.querySelector("[name='production']");
            const hourEl = document.querySelector("[name='hour']");
            const weekendEl = document.querySelector("[name='weekend']");

            if (!energyEl || !prodEl || !hourEl) {
                return; // Not prediction form
            }

            const energy = parseFloat(energyEl.value);
            const production = parseFloat(prodEl.value);
            const hour = parseInt(hourEl.value, 10);

            let errorMessage = "";
            let focusTarget = null;

            if (isNaN(energy) || energy <= 0) {
                errorMessage = "Energy Consumption must be greater than 0 kWh.";
                focusTarget = energyEl;
            } else if (isNaN(production) || production < 0) {
                errorMessage = "Production Count cannot be negative.";
                focusTarget = prodEl;
            } else if (isNaN(hour) || hour < 0 || hour > 23) {
                errorMessage = "Working / Shift hour must be between 0 and 23.";
                focusTarget = hourEl;
            } else if (weekendEl && weekendEl.value === "") {
                errorMessage = "Please select weekend schedule status.";
                focusTarget = weekendEl;
            }

            if (errorMessage) {
                e.preventDefault();

                let existingError = document.querySelector(".error-message");
                if (existingError) {
                    existingError.textContent = errorMessage;
                } else {
                    const errorBox = document.createElement("div");
                    errorBox.className = "error-message";
                    errorBox.innerHTML = `
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="12"></line>
                            <line x1="12" y1="16" x2="12.01" y2="16"></line>
                        </svg>
                        <span>${errorMessage}</span>
                    `;
                    form.parentNode.insertBefore(errorBox, form);
                }

                if (focusTarget) {
                    focusTarget.focus();
                    focusTarget.scrollIntoView({ behavior: "smooth", block: "center" });
                }
            } else {
                const submitBtn = form.querySelector("button[type='submit']");
                if (submitBtn) {
                    submitBtn.style.opacity = "0.85";
                    submitBtn.innerHTML = `
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;">
                            <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
                            <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"></path>
                        </svg>
                        Calculating CO₂...
                    `;
                }
            }
        });
    }

    // ======================================================================
    // 5. REAL-TIME IOT DASHBOARD LIVE POLLING & CHART
    // ======================================================================
    const trendCanvas = document.getElementById("iotTrendChart");
    let iotChart = null;

    if (trendCanvas && typeof Chart !== "undefined") {
        const ctx = trendCanvas.getContext("2d");
        iotChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: [],
                datasets: [
                    {
                        label: "Energy (kWh)",
                        borderColor: "#0284c7",
                        backgroundColor: "rgba(2, 132, 199, 0.08)",
                        borderWidth: 2,
                        tension: 0.35,
                        fill: true,
                        data: [],
                        yAxisID: "y"
                    },
                    {
                        label: "Calculated CO₂ (kg)",
                        borderColor: "#059669",
                        backgroundColor: "rgba(5, 150, 105, 0.08)",
                        borderWidth: 2,
                        borderDash: [4, 4],
                        tension: 0.35,
                        fill: false,
                        data: [],
                        yAxisID: "y1"
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: "index",
                    intersect: false
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 11 } }
                    },
                    y: {
                        type: "linear",
                        display: true,
                        position: "left",
                        title: { display: true, text: "Energy (kWh)", font: { size: 11 } },
                        grid: { color: "rgba(0, 0, 0, 0.04)" }
                    },
                    y1: {
                        type: "linear",
                        display: true,
                        position: "right",
                        title: { display: true, text: "CO₂ (kg)", font: { size: 11 } },
                        grid: { drawOnChartArea: false }
                    }
                },
                plugins: {
                    legend: { position: "top" }
                }
            }
        });

        // Function to fetch latest telemetry & chart history
        function updateDashboardTelemetry() {
            // 1. Fetch latest IoT status
            fetch("/api/iot/latest")
                .then(res => res.json())
                .then(data => {
                    if (data.status === "success") {
                        const energyEl = document.getElementById("live-energy");
                        const prodEl = document.getElementById("live-production");
                        const hoursEl = document.getElementById("live-hours");
                        const co2El = document.getElementById("live-co2");
                        const forecastEl = document.getElementById("live-forecast");
                        const statusEl = document.getElementById("live-status");
                        const lastSeenEl = document.getElementById("iot-last-seen");
                        const statusTextEl = document.getElementById("iot-status-text");
                        const pulseDot = document.getElementById("iot-pulse-dot");
                        const deviceIdEl = document.getElementById("iot-device-id");

                        const powerEl = document.getElementById("live-power");
                        const voltageEl = document.getElementById("live-voltage");
                        const currentEl = document.getElementById("live-current");
                        const pfEl = document.getElementById("live-pf");
                        const freqEl = document.getElementById("live-freq");
                        const efficiencyEl = document.getElementById("live-efficiency");
                        const sessionEl = document.getElementById("live-session-time");

                        if (energyEl) energyEl.textContent = data.energy_kwh !== undefined ? data.energy_kwh.toFixed(2) : "--.--";
                        if (prodEl) prodEl.textContent = data.production_count !== undefined ? data.production_count : "---";
                        if (hoursEl) hoursEl.textContent = data.operating_hours !== undefined ? data.operating_hours.toFixed(2) : "--.--";
                        if (co2El) co2El.textContent = data.co2_emission !== undefined ? data.co2_emission.toFixed(2) : "--.--";
                        if (forecastEl) forecastEl.textContent = data.forecast_co2 !== undefined ? data.forecast_co2.toFixed(2) : (data.co2_emission ? data.co2_emission.toFixed(2) : "--.--");
                        if (statusEl) {
                            statusEl.textContent = data.machine_status;
                            statusEl.style.color = (data.machine_status === "Running") ? "#059669" : "#64748b";
                        }
                        if (lastSeenEl) lastSeenEl.textContent = data.last_received || "Awaiting telemetry";
                        if (deviceIdEl) deviceIdEl.textContent = data.device_id;

                        if (powerEl) powerEl.textContent = data.power !== undefined ? data.power.toFixed(1) : "--.-";
                        if (voltageEl) voltageEl.textContent = data.voltage !== undefined ? data.voltage.toFixed(1) : "--.-";
                        if (currentEl) currentEl.textContent = data.current !== undefined ? data.current.toFixed(2) : "-.--";
                        if (pfEl) pfEl.textContent = data.power_factor !== undefined ? data.power_factor.toFixed(2) : "0.95";
                        if (freqEl) freqEl.textContent = data.frequency !== undefined ? data.frequency.toFixed(1) : "50.0";
                        if (efficiencyEl) efficiencyEl.textContent = data.energy_per_unit !== undefined ? data.energy_per_unit.toFixed(4) : "0.0000";
                        if (sessionEl) sessionEl.textContent = data.session_duration_minutes !== undefined ? data.session_duration_minutes.toFixed(1) : "0.0";

                        const pzemBadge = document.getElementById("pzem-status-badge");
                        const irBadge = document.getElementById("ir-status-badge");
                        if (pzemBadge) {
                            pzemBadge.textContent = data.is_online ? "Active" : "Standby";
                            pzemBadge.style.color = data.is_online ? "#10b981" : "#94a3b8";
                        }
                        if (irBadge) {
                            irBadge.textContent = data.is_online ? "Armed" : "Standby";
                            irBadge.style.color = data.is_online ? "#10b981" : "#94a3b8";
                        }

                        if (statusTextEl && pulseDot) {
                            statusTextEl.textContent = data.connection_state;
                            if (data.is_online) {
                                pulseDot.style.background = data.is_mock ? "#f59e0b" : "#10b981";
                            } else {
                                pulseDot.style.background = "#94a3b8";
                            }
                        }
                    }
                })
                .catch(err => console.error("Telemetry fetch error:", err));

            // 2. Fetch history for trend chart
            fetch("/api/iot/history")
                .then(res => res.json())
                .then(data => {
                    if (data.status === "success" && iotChart && data.labels.length > 0) {
                        iotChart.data.labels = data.labels;
                        iotChart.data.datasets[0].data = data.energies;
                        iotChart.data.datasets[1].data = data.co2_emissions;
                        iotChart.update("none");
                    }
                })
                .catch(err => console.error("Chart history error:", err));
        }

        // Initial fetch
        updateDashboardTelemetry();

        // Recurring poll every 4 seconds
        setInterval(updateDashboardTelemetry, 4000);

        // Mock simulation button listener
        const mockBtn = document.getElementById("btn-trigger-mock");
        if (mockBtn) {
            mockBtn.addEventListener("click", function () {
                mockBtn.disabled = true;
                mockBtn.textContent = "Injecting...";

                // Generate realistic PZEM electrical values
                const sampleVoltage = (229.0 + Math.random() * 4.0).toFixed(1);
                const sampleCurrent = (2.20 + Math.random() * 0.8).toFixed(2);
                const samplePower = (parseFloat(sampleVoltage) * parseFloat(sampleCurrent) * 0.95).toFixed(1);
                const sampleEnergy = (12.0 + Math.random() * 4.0).toFixed(2);
                const sampleProd = Math.floor(90 + Math.random() * 25);
                const sampleHours = (4.0 + Math.random() * 3.0).toFixed(1);

                fetch("/api/iot/mock", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        voltage: parseFloat(sampleVoltage),
                        current: parseFloat(sampleCurrent),
                        power: parseFloat(samplePower),
                        energy_kwh: parseFloat(sampleEnergy),
                        frequency: 50.0,
                        power_factor: 0.95,
                        production_count: sampleProd,
                        operating_hours: parseFloat(sampleHours),
                        machine_status: "Running"
                    })
                })
                    .then(res => res.json())
                    .then(() => {
                        updateDashboardTelemetry();
                        mockBtn.textContent = "✓ Injected!";
                        setTimeout(() => {
                            mockBtn.disabled = false;
                            mockBtn.textContent = "⚡ Inject Test Reading";
                        }, 1200);
                    })
                    .catch(err => {
                        console.error("Mock injection failed:", err);
                        mockBtn.disabled = false;
                        mockBtn.textContent = "⚡ Inject Test Reading";
                    });
            });
        }

        // Batch counter reset button listener
        const resetBtn = document.getElementById("btn-reset-prod");
        if (resetBtn) {
            resetBtn.addEventListener("click", function () {
                if (confirm("Reset current batch production counter to zero?")) {
                    resetBtn.disabled = true;
                    fetch("/api/iot/reset_production", { method: "POST" })
                        .then(res => res.json())
                        .then(() => {
                            updateDashboardTelemetry();
                            resetBtn.disabled = false;
                        })
                        .catch(() => {
                            resetBtn.disabled = false;
                        });
                }
            });
        }
    }

    // ======================================================================
    // 6. GRAPH LIGHTBOX MODAL (DASHBOARD)
    // ======================================================================
    const graphImgs = document.querySelectorAll(".graph-card img, .graph-img-wrapper img");

    if (graphImgs.length > 0) {
        let modal = document.querySelector(".lightbox-modal");
        if (!modal) {
            modal = document.createElement("div");
            modal.className = "lightbox-modal";
            modal.innerHTML = `
                <div class="lightbox-content">
                    <button class="lightbox-close" aria-label="Close image modal">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                    <img src="" alt="Enlarged visualization">
                </div>
            `;
            document.body.appendChild(modal);

            const closeBtn = modal.querySelector(".lightbox-close");
            const modalImg = modal.querySelector("img");

            const closeModal = () => {
                modal.classList.remove("active");
            };

            closeBtn.addEventListener("click", closeModal);
            modal.addEventListener("click", (e) => {
                if (e.target === modal) closeModal();
            });

            document.addEventListener("keydown", (e) => {
                if (e.key === "Escape" && modal.classList.contains("active")) {
                    closeModal();
                }
            });

            graphImgs.forEach(img => {
                img.style.cursor = "zoom-in";
                img.addEventListener("click", function () {
                    modalImg.src = this.src;
                    modalImg.alt = this.alt || "Visualization Preview";
                    modal.classList.add("active");
                });
            });
        }
    }
});