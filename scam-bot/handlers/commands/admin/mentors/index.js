const { Markup } = require("telegraf");

const { Mentors } = require("../../../../database/index")

module.exports = async (ctx) => {
  try {
    const mentorsCount = await Mentors.count({
        status: true
    })

    return ctx
      .editMessageText(
        `<b>🗂️ Текущий раздел:</b>
╰ 👩‍🏫 Панель администратора -> Наставники

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

╭ 👨🏼‍🏫 <b>Всего наставников:</b> ${mentorsCount}
╰ 🔗 <b>Процентная ставка:</b> ${ctx.state.settings.mentorPercent}%`,
        {
          parse_mode: "HTML",
          disable_web_page_preview: true,
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.callbackButton("📄 Список наставников", `admin_mentors_list`),
              Markup.callbackButton("⚖️ Изменить процент", `admin_mentors_percent`),
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