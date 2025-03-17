function drawChart(history, prediction) {
    const ctx = document.getElementById("priceChart").getContext("2d");

    if (chartInstance) {
        chartInstance.destroy();
    }

    const labels = history.map((_, i) => `День ${i + 1}`);
    const predictionLabels = prediction.map((_, i) => `Прогноз ${i + 1}`);

    chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: [...labels, ...predictionLabels],
            datasets: [
                {
                    label: "История",
                    data: history,
                    borderColor: "#3861fb",
                    tension: 0.4,
                    fill: false
                },
                prediction.length ? {
                    label: "Прогноз",
                    data: [...Array(history.length - 1).fill(null), ...prediction],
                    borderColor: "#ffffff",
                    borderDash: [5, 5],
                    tension: 0.4,
                    fill: false
                } : null
            ].filter(Boolean)
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    title: { display: true, text: "Цена (₽)" }
                },
                xAxes: [{ gridLines: { color: "#131c2b" } }],
                yAxes: [{ gridLines: { color: "#131c2b" } }]
            },
            plugins: {
                legend: { position: "top" }
            }
        }
    });

    document.getElementById("predictBtn").disabled = prediction.length > 0;
}