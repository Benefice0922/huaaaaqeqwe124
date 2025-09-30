const { Markup } = require("telegraf");

module.exports = async (ctx) => {
  try {
    return ctx
      .editMessageText(
        `🗂️ <b>Текущий раздел:</b>
╰ 💭 Профиль -> Чаты

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.urlButton("💬 Чат", ctx.state.settings.workerChatUrl),
              Markup.urlButton("💸 Выплаты", ctx.state.settings.payChatUrl),
            ],
            [Markup.callbackButton("< Назад", "menu")],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};