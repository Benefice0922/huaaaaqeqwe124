const { Markup } = require("telegraf");

const { Mentors, Profits, users } = require("../../../../database/index")

module.exports = async (ctx) => {
  try {
    const mentor = await Mentors.findOne({
        where: {
            id: ctx.match[1]
        }
    })

    const profitsCount = await Profits.count({
        where: {
            mentorId: mentor.workerId
        }
    })

    const usersCount = await users.count({
        where: {
            mentorId: mentor.workerId
        }
    })

    return ctx
      .editMessageText(
        `🧑‍🏫 <b>Наставник <a href="tg://user?id=${mentor.workerId}">${mentor.username}</a></b>

💰 <b>Колиество профитов с наставником:</b> ${profitsCount}
👨‍🎓 <b>Количество учеников:</b> ${usersCount}

📝 <b>Описание наставника:</b>
${mentor.about}`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("👨‍🎓 Стать учеником", `teach_${ctx.match[1]}`)],
            [Markup.callbackButton("< Назад", "mentors")],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};