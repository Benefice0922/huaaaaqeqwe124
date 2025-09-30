const { Markup } = require("telegraf");

module.exports = async (ctx) => {
  try {
    return ctx
      .editMessageText(
        `🗂️ <b>Текущий раздел:</b>
╰ 💳 Профиль -> Кошелёк

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

╭ ▫️ Валюта: ${ctx.state.user.wallet == null ? "Не выбрана" : ctx.state.user.wallet.split("&")[0]}
╰ ▫️ Адрес: ${ctx.state.user.wallet == null ? "Не установлен" : ctx.state.user.wallet.split("&")[1]}`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("⚙️ Сменить", "changeWallet")],
            [Markup.callbackButton("< Назад", "profile")],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};