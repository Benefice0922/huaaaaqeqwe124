const { Markup } = require("telegraf");

const { Mentors, Profits, users } = require("../../../../database/index");

module.exports = async (ctx) => {
  try {
    const mentor = await Mentors.findOne({
      where: {
        id: ctx.match[1],
      },
    });

    const profits = await Profits.count({
      where: {
        mentorId: mentor.workerId,
      },
    });

    const mentorProfits = await Profits.sum("eurAmount", {
      where: {
        mentorId: mentor.workerId,
      },
    });

    const Users = await users.count({
      where: {
        mentorId: mentor.workerId
      }
    })

    return ctx
      .editMessageText(
        `<b>🗂️ Текущий раздел:</b>
╰ 💁🏼‍♂️ Панель администратора -> Наставники -> Список наставников -> @${
          mentor.username
        }

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

╭ ♻️ <b>Всего профитов у учеников:</b> ${profits} шт.
├ 👩‍🎓 <b>Всего учеников:</b> ${Users}
╰ 💰 <b>Заработал с учеников:</b> € ${
          mentorProfits == null
            ? "0.00"
            : ((mentorProfits / 100) * parseInt(mentor.percent)).toFixed(2)
        }
        
╭ ⚖️ <b>Процент наставника:</b> ${mentor.percent}%
╰ 📝 <b>О наставнике:</b>

${mentor.about}`,
        {
          parse_mode: "HTML",
          disable_web_page_preview: true,
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.callbackButton(
                "⚖️ Изменить процент",
                `admin_mentor_${mentor.id}_changePercent`
              ),
              Markup.callbackButton(
                "✏️ Изменить описание",
                `admin_mentor_${mentor.id}_changeAbout`
              ),
            ],
            [
              Markup.callbackButton(
                "❌ Удалить",
                `admin_mentor_${mentor.id}_destroy`
              ),
            ],
            [Markup.callbackButton("< Назад", `admin_mentors`)],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};