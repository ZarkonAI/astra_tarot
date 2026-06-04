window.AstraTelegram = {
  tg: window.Telegram ? window.Telegram.WebApp : null,
  init() { if (this.tg) { this.tg.ready(); this.tg.expand(); } },
  getInitData() { return this.tg ? this.tg.initData : ""; },
  getUserIdForDev() { const user = this.tg && this.tg.initDataUnsafe ? this.tg.initDataUnsafe.user : null; return user ? user.id : 0; }
};
window.AstraTelegram.init();
