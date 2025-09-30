const { Markup } = require("telegraf");

const { Mentors, users } = require("../../../database/index");

module.exports = async (ctx) => {
  try {
    var status = ctx.match[1];
    var workerId = ctx.match[2];

    const mentor = await Mentors.findOne({
      where: {
        id: ctx.match[2],
      },
    });

    if (status == "decline") {
      await Mentors.destroy({
        where: {
          workerId: mentor.workerId,
        },
      });
      await ctx.telegram.sendMessage(
        mentor.workerId,
        `❌ <b>Ваша заявка на наставника была отклонена</b>`,
        {
          parse_mode: "HTML",
        }
      );
    } else {
      await mentor.update({
        status: true,
      });
      await users.update({
        status: 3
      }, {
        where: {
          id: mentor.workerId
        }
      })

      await ctx.telegram.sendMessage(
        mentor.workerId,
        `<b>🥳 Ваша заявка на наставника была одобрена!</b>`,
        {
          parse_mode: "HTML",
        }
      );
    }

    await ctx
      .editMessageText(
        `Адмнистратор @${ctx.from.username} ${
          status == "accept" ? "одобрил" : "отклонил"
        } заявку @${mentor.username} на наставника`
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};