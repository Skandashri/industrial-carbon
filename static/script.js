// ================================
// Industrial Carbon Forecasting
// script.js
// ================================

document.addEventListener("DOMContentLoaded", function () {

    console.log("Industrial Carbon Forecasting Loaded");

    // ==========================
    // Highlight Current Menu
    // ==========================

    let currentPage = window.location.pathname;

    let links = document.querySelectorAll("nav a");

    links.forEach(link => {

        if (link.getAttribute("href") === currentPage) {

            link.style.color = "#ffe66d";

        }

    });

    // ==========================
    // Prediction Form Validation
    // ==========================

    let form = document.querySelector("form");

    if (form) {

        form.addEventListener("submit", function (e) {

            let energy =
                parseFloat(document.querySelector("[name='energy']").value);

            let temp =
                parseFloat(document.querySelector("[name='temperature']").value);

            let humidity =
                parseFloat(document.querySelector("[name='humidity']").value);

            let production =
                parseFloat(document.querySelector("[name='production']").value);

            if (energy <= 0) {

                alert("Energy Consumption must be greater than 0.");

                e.preventDefault();

                return;

            }

            if (production <= 0) {

                alert("Production Output must be greater than 0.");

                e.preventDefault();

                return;

            }

            if (temp < -20 || temp > 100) {

                alert("Temperature should be between -20°C and 100°C.");

                e.preventDefault();

                return;

            }

            if (humidity < 0 || humidity > 100) {

                alert("Humidity must be between 0 and 100%.");

                e.preventDefault();

                return;

            }

        });

    }

});