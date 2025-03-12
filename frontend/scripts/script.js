const stocks = [
    { name: "Сбербанк России", ticker: "SBER", price: 316.55, history: [300, 310, 315, 320, 316.55] },
    { name: "Газпром", ticker: "GAZP", price: 173.3, history: [160, 165, 170, 172, 173.3] },
    { name: "Т технологии", ticker: "T", price: 3385.8, history: [3300, 3320, 3350, 3370, 3385.8] },
];

const news1 = ["Новость 1", "Новость 2", "Новость 3", "Новость 4", "Новость 5"];
const news2 = ["Новость 1", "Новость 2", "Новость 3", "Новость 4", "Новость 5"];

let currentStock = null;
let chartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
    loadStocks();
    document.getElementById("predictBtn").addEventListener("click", predictPrice);

    // Обработка кнопок "Назад" и "Вперёд"
    window.onpopstate = function (event) {
        if (event.state && event.state.page === "stock") {
            openStock(event.state.stock, false);
        } else {
            showScreen1(false);
        }
    };
});

function loadStocks() {
    const stockList = document.getElementById("stockList");
    stocks.forEach(stock => {
        let li = document.createElement("li");
        li.textContent = `${stock.name} - ${stock.price} ₽`;
        li.onclick = () => openStock(stock);
        stockList.appendChild(li);
    });

    const newsList = document.getElementById("newsList");
    news1.forEach(n => {
        let li = document.createElement("li");
        li.textContent = n;
        newsList.appendChild(li);
    });
}

function openStock(stock, updateHistory = true) {
    currentStock = stock;
    document.getElementById("screen1").style.display = "none";
    document.getElementById("screen2").style.display = "flex";
    document.getElementById("stockName").textContent = stock.name;
    document.getElementById("stockPrice").textContent = stock.price;

    const stockNews = document.getElementById("stockNews");
    news2.forEach(n => {
        let li = document.createElement("li");
        li.textContent = n;
        stockNews.appendChild(li);
    });

    drawChart(stock.history, []);

    if (updateHistory) {
        history.pushState({ page: "stock", stock }, "", `#${stock.ticker}`);
    }
}

function showScreen1(updateHistory = true) {
    document.getElementById("screen1").style.display = "flex";
    document.getElementById("screen2").style.display = "none";

    if (updateHistory) {
        history.pushState({ page: "home" }, "", "/");
    }
}

function predictPrice() {
    if (!currentStock) return;

    const lastPrice = currentStock.history[currentStock.history.length - 1];
    const prediction = [
        lastPrice * 1.01,
        lastPrice * 1.02,
        lastPrice * 1.03,
        lastPrice * 1.05
    ];

    drawChart(currentStock.history, prediction);
}
