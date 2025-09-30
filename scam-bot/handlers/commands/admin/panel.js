const { Markup } = require("telegraf");
const { Profits, users, items } = require("../../../database/index");

module.exports = async (ctx) => {
  try {
    const kassa = await Profits.sum("eurAmount");
    const Users = await users.count({
      where: {
        status: 1,
      },
    });
    const Items = await items.count();

    await ctx.deleteMessage().catch((err) => err);

    return ctx
      .replyWithHTML(
        `<b>🗂️ Текущий раздел:</b>
╰ 👨🏻‍💻 Панель администратора

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

╭ 🎾 <b>Статус работы:</b> ${
          ctx.state.settings.work == true ? "WORK" : "STOP WORK"
        }
╰ 🏦 <b> Касса:</b> € ${kassa == null ? "0.00" : kassa.toFixed(2)}

╭ 👩‍🚒 <b>Всего воркеров:</b> ${Users}
├ ⚖️ <b>Процентная ставка:</b> ${ctx.state.settings.percent} %
╰ 📦 <b>Активных фишингов:</b> ${Items}`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("📪 Рассылка", "adminAlert")],
            [
              Markup.callbackButton("🌐 Домены", "admin_domains"),
              Markup.callbackButton("👩‍🏫 Наставники", "admin_mentors"),
            ],
            [
              Markup.callbackButton("📦 Объявления", "admin_items"),
              Markup.callbackButton("💰 Профиты", "admin_profits"),
            ],
            [Markup.callbackButton("⚙️ Настройки проекта", "admin_settings")],
            [Markup.callbackButton("♻️ Скрыть", "hide")],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};
