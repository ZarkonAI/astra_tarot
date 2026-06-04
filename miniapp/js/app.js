const screens = { menu: document.getElementById("screen-menu"), question: document.getElementById("screen-question"), loading: document.getElementById("screen-loading"), result: document.getElementById("screen-result") };
const spreadTitles = { daily_card: "Карта дня", quick_reading: "Быстрый расклад", heart_reading: "Сердечный расклад", money_path: "Денежный путь", deep_reading: "Глубокий расклад" };
let selectedSpread = null;
function showScreen(name) { Object.values(screens).forEach(screen => screen.classList.remove("active")); screens[name].classList.add("active"); }
document.querySelectorAll(".spread-card").forEach(button => { button.addEventListener("click", () => { selectedSpread = button.dataset.spread; document.getElementById("selected-title").textContent = spreadTitles[selectedSpread] || "Расклад"; document.getElementById("question").value = selectedSpread === "daily_card" ? "Карта дня" : ""; showScreen("question"); }); });
document.getElementById("back-to-menu").addEventListener("click", () => showScreen("menu"));
document.getElementById("new-reading").addEventListener("click", () => showScreen("menu"));
document.getElementById("draw-btn").addEventListener("click", async () => {
  const question = document.getElementById("question").value.trim();
  if (!selectedSpread) { alert("Сначала выберите расклад"); return; }
  if (selectedSpread !== "daily_card" && question.length < 5) { alert("Сформулируйте вопрос чуть подробнее"); return; }
  showScreen("loading");
  try {
    const data = await window.AstraApi.generateReading(selectedSpread, question);
    if (!data.ok) {
      document.getElementById("result-title").textContent = "Astra остановила расклад";
      document.getElementById("drawn-cards").innerHTML = "";
      document.getElementById("answer").textContent = data.message || "Попробуйте немного позже.";
      showScreen("result"); return;
    }
    document.getElementById("result-title").textContent = data.spread.title;
    document.getElementById("drawn-cards").innerHTML = data.cards.map((card, index) => `<div class="drawn-card"><b>${index + 1}. ${card.name}</b><br><small>${card.keywords}</small></div>`).join("");
    document.getElementById("answer").textContent = data.answer;
    showScreen("result");
  } catch (error) {
    document.getElementById("result-title").textContent = "Ошибка";
    document.getElementById("drawn-cards").innerHTML = "";
    document.getElementById("answer").textContent = "Звезда временно скрылась за облаками. Попробуйте немного позже.";
    showScreen("result");
  }
});
