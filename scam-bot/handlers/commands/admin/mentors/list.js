const { Markup } = require("telegraf");

const { Mentors } = require("../../../../database/index")

module.exports = async (ctx) => {
  try {
    const { count, rows } = await Mentors.findAndCountAll({
      where: {
        status: true
      }
    })

    var buttons = rows.map((v, i) => [
        Markup.callbackButton(
          `👨🏼‍🏫 ${i + 1}. ${v.username}`, `admin_mentor_${v.id}`
        ),
      ]);

      if(count == 0) return ctx.answerCbQuery("🤖 На следующей странице ничего нет", true).catch((err) => err);

    return ctx
      .editMessageText(
        `<b>🗂️ Текущий раздел:</b>
╰ 📄 Панель администратора -> Наставники -> Список наставников

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

╭ 👨🏼‍🏫 <b>Всего наставников:</b> ${count}
╰ 🔗 <b>Процентная ставка:</b> ${ctx.state.settings.mentorPercent}%`,
        {
          parse_mode: "HTML",
          disable_web_page_preview: true,
          reply_markup: Markup.inlineKeyboard([
            ...buttons,
            [Markup.callbackButton("< Назад", "admin_mentors")],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};