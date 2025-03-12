function drawChart(history, prediction) {
    const ctx = document.getElementById("priceChart").getContext("2d");

    if (chartInstance) {
        chartInstance.destroy();
    }

    const historyLabels = history.map((_, i) => `Day ${i + 1}`);
    const predictionLabels = prediction.length
        ? prediction.map((_, i) => `Future ${i + 1}`)
        : ["Future 1", "Future 2", "Future 3", "Future 4"];

    const lastHistoryValue = history[history.length - 1];

    chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: [...historyLabels, ...predictionLabels],
            datasets: [
                {
                    label: "Цена",
                    data: [...history, lastHistoryValue],
                    borderColor: "blue",
                    fill: false,
                    borderDash: [],
                },
                {
                    label: "Прогноз",
                    data: [...Array(history.length).fill(null), lastHistoryValue, ...prediction],
                    borderColor: "red",
                    fill: false,
                    borderDash: [5, 5],
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { display: true },
                y: { display: true }
            }
        }
    });
}
