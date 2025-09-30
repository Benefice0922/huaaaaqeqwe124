const { Markup } = require("telegraf");

const { Mentors } = require("../../../../database/index")

module.exports = async (ctx) => {
  try {
    const mentors = await Mentors.findAll({
        where: {
            status: true
        }
    })

    var buttons = mentors.map((v, i) => [
            Markup.callbackButton(`${i + 1}. ${v.username == null ? v.id : v.username}`, `mentor_${v.id}`)
        ]
        )

    if (buttons.length < 1) {
        buttons = [[Markup.callbackButton("Список наставников пуст", "none")]];
    }

    return ctx
      .editMessageText(
        `🗂️ <b>Текущий раздел:</b>
    ╰ 🧑‍🏫 Наставники

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            ...buttons,
            [Markup.callbackButton("🧑‍🏫 Стать наставником", "reqMentor")],
            [Markup.callbackButton("< Назад", "menu")],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};