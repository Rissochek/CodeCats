const API_URLS = {
    companyNews: 'http://localhost:8006/get_company_news',
    lastNews: 'http://localhost:8004/get_last_news',
    lastPrices: 'http://localhost:8003/get_last_prices'
};

const modal = document.getElementById("newsModal");

let currentStock = null;
let chartInstance = null;


function showLoader() {
    document.getElementById("loader").style.display = "flex";
}


function hideLoader() {
    document.getElementById("loader").style.display = "none";
}


document.addEventListener("DOMContentLoaded", () => {
    loadStocks();
    document.getElementById("predictBtn").addEventListener("click", predictPrice);
    document.getElementById("resetChartBtn").addEventListener("click", resetChart);
    window.onpopstate = handlePopState;
});


async function fetchStockData() {
    try {
        showLoader();
        const responses = await Promise.all([
            fetch(API_URLS.lastPrices, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ company: "SBER", number_of_prices: 5 })
            }),
            fetch(API_URLS.lastPrices, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ company: "GAZP", number_of_prices: 5 })
            }),
            fetch(API_URLS.lastPrices, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ company: "T", number_of_prices: 5 })
            })
        ]);

        const stocks = await Promise.all(responses.map(r => r.json()));
        return stocks.map((prices, i) => ({
            name: ["Сбербанк России", "Газпром", "Т технологии"][i],
            ticker: ["SBER", "GAZP", "T"][i],
            price: prices[prices.length - 1].close,
            history: prices.map(p => p.close),
            news: []
        }));
    } catch (error) {
        console.error("Fetch error:", error);
        return [];
    } finally {
        hideLoader();
    }
}


async function loadStocks() {
    try {
        showLoader();
        const [stocksData, mainNewsResponse] = await Promise.all([
            fetchStockData(),
            fetch(API_URLS.lastNews, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache'
                },
                body: JSON.stringify({
                    number_of_news: 5,
                    timestamp: Date.now()
                })
            })
        ]);


        const uniqueNews = mainNewsResponse.ok
            ? (await mainNewsResponse.json()).filter((news, index, self) =>
                index === self.findIndex(n => n.link === news.link)
            )
            : [];


        const stockList = document.getElementById("stockList");
        stockList.innerHTML = stocksData.map(stock => `
            <li>${stock.name} - ${stock.price} ₽</li>
        `).join('');


        document.querySelectorAll("#stockList li").forEach((li, index) => {
            li.addEventListener("click", () => openStock(stocksData[index]));
        });


        const newsList = document.getElementById("newsList");
        newsList.innerHTML = uniqueNews.map(news => `
            <li class="news-item">
                ${news.title} - ${formatDate(news.datetime)}
            </li>
        `).join('');


        document.querySelectorAll('.news-item').forEach((item, index) => {
            item.addEventListener('click', () => showNewsModal(uniqueNews[index]));
        });

    } catch (error) {
        console.error("Ошибка загрузки:", error);
        alert("Не удалось загрузить данные");
    } finally {
        hideLoader();
    }
}


async function openStock(stock, updateHistory = true) {
    try {
        showLoader();

        const [newsResponse] = await Promise.all([
            fetch(API_URLS.companyNews, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache'
                },
                body: JSON.stringify({
                    company: stock.ticker,
                    number_of_news: 5,
                    timestamp: Date.now()
                })
            })
        ]);

        if (!newsResponse.ok) throw new Error("Ошибка API");
        const companyNews = await newsResponse.json();


        const uniqueNews = companyNews.filter((news, index, self) =>
            index === self.findIndex(n => n.link === news.link)
        );

        currentStock = {
            ...stock,
            news: uniqueNews
        };


        const stockNews = document.getElementById("stockNews");
        stockNews.innerHTML = currentStock.news.map(news => `
            <li class="news-item">
                ${news.title} - ${formatDate(news.datetime)}
            </li>
        `).join('');


        document.querySelectorAll('#stockNews .news-item').forEach((item, index) => {
            item.addEventListener('click', () => showNewsModal(currentStock.news[index]));
        });


        document.getElementById("screen1").style.display = "none";
        document.getElementById("screen2").style.display = "flex";
        document.getElementById("stockName").textContent = currentStock.name;
        document.getElementById("stockPrice").textContent = currentStock.price;
        drawChart(currentStock.history, []);

        if (updateHistory) {
            history.pushState({ page: "stock", stock: currentStock }, "", `#${stock.ticker}`);
        }

    } catch (error) {
        console.error("Ошибка загрузки:", error);
        alert("Не удалось загрузить данные");
    } finally {
        hideLoader();
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

    try {
        showLoader();
        await new Promise(resolve => setTimeout(resolve, 800));
        const lastPrice = currentStock.history.slice(-1)[0];
        const prediction = [lastPrice * 1.01, lastPrice * 1.02, lastPrice * 1.03];
        drawChart(currentStock.history, prediction);
    } finally {
        hideLoader();
    }
}


function resetChart() {
    if (!currentStock) return;
    drawChart(currentStock.history, []);
    document.getElementById("predictBtn").disabled = false;
}


function formatDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}


function showNewsModal(news) {
    document.body.classList.add('modal-open');
    document.getElementById("modalTitle").textContent = news.title;
    document.getElementById("modalText").textContent = news.article_text;
    document.getElementById("newsModal").style.display = "block";
}


function closeModal() {
    document.body.classList.remove('modal-open');
    document.getElementById("newsModal").style.display = "none";
}


window.onclick = (e) => {
    if (e.target === modal) closeModal();
}