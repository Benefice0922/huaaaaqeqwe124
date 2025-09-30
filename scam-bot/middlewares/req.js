const { Requests, users } = require("../database/index")

const { Markup } = require("telegraf");

module.exports = async (ctx, next) => {
  try {
    if (ctx.state.req == true || ctx.state.user.status == 0) {
      return ctx.replyWithHTML(
        `💁🏻‍♂️ <b>Привет,</b> ${ctx.from.first_name}<b>!</b>
🦋 <b>Перед тем, как продолжить использование бота тебе надо подать заявку!</b>`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("🔹 Подать заявку! 🔹", "sendRequest")],
          ]),
        }
      );
    }

    return next().catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};