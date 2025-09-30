const { Markup } = require("telegraf");

const { items } = require("../../../../database/index");

module.exports = async (ctx) => {
  try {
    const type = ctx.match[1];

    const { count, rows } = await items.findAndCountAll({
      where: {
        status: type == "pay" ? 1 : type == "receive" ? 2 : 3,
        workerId: ctx.from.id,
      },
      order: [["createdAt", "DESC"]],
      limit: 10,
    });

    if (count == 0)
      return ctx
        .answerCbQuery("🤖 На следующей странице ничего нет", true)
        .catch((err) => err);

    var buttons = rows.map((v, i) => [
      Markup.callbackButton(
        `${type == "pay" ? "🚚" : type == "receive" ? "📦" : "🛫"} ${i + 1}. ${
          v.title
        } | #${v.id}`,
        `ad_${v.id}`
      ),
    ]);

    return ctx
      .editMessageText(
        `🗂️ <b>Текущий раздел:</b>
╰ ${
          type == "pay" ? "🚚" : type == "receive" ? "📦" : "🛫"
        } Профиль -> Ссылки -> ${
          type == "pay"
            ? "Оплата"
            : type == "receive"
            ? "Получение"
            : "Бронирование"
        } (${count} шт.)

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            ...buttons,
            [Markup.callbackButton("< Назад", "myAds")],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};