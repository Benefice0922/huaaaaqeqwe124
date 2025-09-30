const { Markup } = require("telegraf");

module.exports = async (ctx) => {
  try {
    return ctx
      .editMessageText(
        `🗂️ <b>Текущий раздел:</b>
╰ 🧾 Профиль -> Ссылки

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.callbackButton("🚚 Оплата", "my_payAds"),
              Markup.callbackButton("📦 Получение", "my_receiveAds"),
            ],
            [
              Markup.callbackButton("🛫 Бронирования", "my_otherAds"),
            ],
            [Markup.callbackButton("🗑️ Удалить все", "clearMyAds")],
            [Markup.callbackButton("< Назад", "menu")],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};