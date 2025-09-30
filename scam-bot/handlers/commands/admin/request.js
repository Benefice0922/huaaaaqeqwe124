const { Markup } = require("telegraf");

const { users, Requests } = require("../../../database/index");

function genTag() {
  var result = '';
  var characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
  var charactersLength = characters.length;
  for (var i = 0; i < 8; i++) {
      result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }
  return result;
}

module.exports = async (ctx) => {
  try {
    var status = ctx.match[1];
    var workerId = ctx.match[2];

    await users.update(
      {
        status: status == "accept" ? 1 : 2,
        tag: genTag()
      },
      {
        where: {
          id: workerId,
        },
      }
    );

    await Requests.update(
      {
        status: status == "accept" ? 1 : 2,
      },
      {
        where: {
          workerId: workerId,
        },
      }
    );

    const worker = await users.findOne({
      where: {
        id: workerId,
      },
    });

    await ctx
      .editMessageText(
        `Адмнистратор @${ctx.from.username} ${
          status == "accept" ? "одобрил" : "отклонил"
        } заявку @${worker.username}`
      )
      .catch((err) => err);

    if (status == "decline")
      return ctx.telegram.sendMessage(
        workerId,
        `❌ <b>Ваша заявка была отклонена</b>`, {
            parse_mode: "HTML"
        }
      );

    await ctx.telegram.sendMessage(
      workerId,
      `🥳 <b>Ваша заявка была одобрена!
    
ℹ️ Для дальнейшей работы с ботом вам необходимо вступить в чат воркеров</b>`,
      {
        parse_mode: "HTML",
        reply_markup: Markup.inlineKeyboard([
          [
            Markup.urlButton("Чат воркеров", ctx.state.settings.workerChatUrl),
            Markup.urlButton("Выплаты", ctx.state.settings.payChatUrl),
          ],
          [Markup.callbackButton("< В меню", "menu")]
        ]),
      }
    );
  } catch (err) {
    console.log(err);
  }
};