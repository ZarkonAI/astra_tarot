window.AstraApi = {
  async generateReading(spreadType, question) {
    const payload = { spread_type: spreadType, question, init_data: window.AstraTelegram.getInitData(), telegram_id: window.AstraTelegram.getUserIdForDev() };
    const response = await fetch("/api/readings/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    return response.json();
  }
};
