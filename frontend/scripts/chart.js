function drawChart(history, prediction) {
    const ctx = document.getElementById("priceChart").getContext("2d");

    if (window.chartInstance) {
        window.chartInstance.destroy();
    }

    const candleData = history.map(data => ({
        x: new Date(data.begin),
        o: parseFloat(data.open),
        h: parseFloat(data.high),
        l: parseFloat(data.low),
        c: parseFloat(data.close)
    }));

    const datasets = [{
        label: "История",
        data: candleData,
        type: 'candlestick',
        color: {
            up: "#00ff00",
            down: "#ff0000",
            unchanged: "#ffffff"
        },
        barPercentage: 0.5,
        maxBarThickness: 10
    }];

    let allDates = candleData.map(d => d.x.getTime());

    if (prediction.length) {
        const lastDate = new Date(history[history.length - 1].begin);
        const predictionData = prediction.map((price, i) => {
            const forecastDate = new Date(lastDate.getTime() + (i + 1) * 3600000);
            return { x: forecastDate, y: parseFloat(price) };
        });
        datasets.push({
            label: "Прогноз",
            data: predictionData,
            type: 'line',
            borderColor: "#ffffff",
            tension: 0.4,
            fill: false,
            pointRadius: 0
        });
        allDates = allDates.concat(predictionData.map(d => d.x.getTime()));
    }

    const minDate = new Date(Math.min(...allDates) - 1800000); // Запас в 0.5 часа слева
    const maxDate = new Date(Math.max(...allDates) + 1800000); // Запас в 0.5 часа справа

    window.chartInstance = new Chart(ctx, {
        type: 'candlestick',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: "time",
                    time: {
                        unit: "hour",
                        displayFormats: {
                            hour: "dd MMM HH:mm"
                        }
                    },
                    min: minDate,
                    max: maxDate,
                    offset: true,
                    ticks: {
                        source: 'data',
                        autoSkip: false,
                        maxRotation: 45,
                        minRotation: 45,
                        color: "#ffffff",
                        callback: function (value, index, values) {
                            if (index % 3 === 0) {
                                const date = new Date(value);
                                return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
                            }
                            return null;
                        }
                    },
                    grid: {
                        color: "#323546"
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
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

    document.getElementById("predictBtn").disabled = prediction.length > 0;
}