function drawChart(history, prediction) {
    const ctx = document.getElementById("priceChart").getContext("2d");

    if (chartInstance) {
        chartInstance.destroy();
    }

    const labels = history.map((_, i) => `Час ${i + 1}`);
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
                    tension: 0.4,
                    fill: false
                } : null
            ].filter(Boolean)
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: {
                        color: "#323546"
                    },
                    ticks: {
                        color: "#ffffff"
                    }
                },
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        color: "#ffffff",
                        text: "Цена (₽)"
                    },
                    grid: {
                        color: "#323546"
                    },
                    ticks: {
                        color: "#ffffff"
                    }
                },
            },
            plugins: {
                legend: {
                    position: "top",
                    labels: {
                        color: "#ffffff"
                    }
                }
            }
        }
    });

    document.getElementById("predictBtn").disabled = prediction.length > 0;
}