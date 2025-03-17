const stocks = [
    {
        name: "Сбербанк России",
        ticker: "SBER",
        price: 316.55,
        history: [300, 310, 315, 320, 316.55],
        news: ["Сбербанк запускает новый сервис", "Дивиденды за 2023 год утверждены"]
    },
    {
        name: "Газпром",
        ticker: "GAZP",
        price: 173.3,
        history: [160, 165, 170, 172, 173.3],
        news: ["Газпром увеличил экспорт", "Строительство нового газопровода"]
    },
    {
        name: "Т технологии",
        ticker: "T",
        price: 3385.8,
        history: [3300, 3320, 3350, 3370, 3385.8],
        news: ["Запуск новой платформы", "Партнёрство с международной компанией"]
    }
];

let currentStock = null;
let chartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
    loadStocks();
    document.getElementById("predictBtn").addEventListener("click", predictPrice);
    document.getElementById("resetChartBtn").addEventListener("click", resetChart);
    window.onpopstate = handlePopState;
});

async function fetchStockData() {
    return new Promise(resolve => setTimeout(() => resolve(stocks), 300));
}

async function loadStocks() {
    try {
        const data = await fetchStockData();
        const stockList = document.getElementById("stockList");
        stockList.innerHTML = "";

        data.forEach(stock => {
            const li = document.createElement("li");
            li.textContent = `${stock.name} - ${stock.price} ₽`;
            li.onclick = () => openStock(stock);
            stockList.appendChild(li);
        });

        const newsList = document.getElementById("newsList");
        newsList.innerHTML = "";
        data[0].news.forEach(n => {
            const li = document.createElement("li");
            li.textContent = n;
            newsList.appendChild(li);
        });
    } catch (error) {
        console.error("Ошибка загрузки:", error);
    }
}

function openStock(stock, updateHistory = true) {
    currentStock = stock;
    document.getElementById("screen1").style.display = "none";
    document.getElementById("screen2").style.display = "flex";

    document.getElementById("stockName").textContent = stock.name;
    document.getElementById("stockPrice").textContent = stock.price;

    const stockNews = document.getElementById("stockNews");
    stockNews.innerHTML = "";
    stock.news.forEach(n => {
        const li = document.createElement("li");
        li.textContent = n;
        stockNews.appendChild(li);
    });

    drawChart(stock.history, []);

    if (updateHistory) {
        history.pushState({ page: "stock", stock }, "", `#${stock.ticker}`);
    }
}

function handlePopState(event) {
    if (event.state?.page === "stock") {
        openStock(event.state.stock, false);
    } else {
        showScreen1(false);
    }
}

function showScreen1(updateHistory = true) {
    document.getElementById("screen1").style.display = "flex";
    document.getElementById("screen2").style.display = "none";

    if (updateHistory) {
        history.pushState({ page: "home" }, "", "/");
    }
}

async function predictPrice() {
    if (!currentStock) return;

    document.getElementById("loader").style.display = "block";
    try {
        await new Promise(resolve => setTimeout(resolve, 800));
        const lastPrice = currentStock.history.slice(-1)[0];
        const prediction = [lastPrice * 1.01, lastPrice * 1.02, lastPrice * 1.03];
        drawChart(currentStock.history, prediction);
    } finally {
        document.getElementById("loader").style.display = "none";
    }
}

function resetChart() {
    if (!currentStock) return;
    drawChart(currentStock.history, []);
    document.getElementById("predictBtn").disabled = false;
}