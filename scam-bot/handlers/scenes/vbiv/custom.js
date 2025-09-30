const { Markup } = require("telegraf");
const WizardScene = require("telegraf/scenes/wizard");

const { Logs } = require("../../../database/index")

module.exports = new WizardScene(
  "customError",
  async (ctx) => {
    try {
      await ctx
        .replyWithHTML(`<b>✍️ Введи текст ошибки</b>`, {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("< Отмена", "cancel")],
          ]),
        })
        .catch((err) => err);
      return ctx.wizard.next();
    } catch (err) {
      console.log(err);
      try {
        await ctx.answerCbQuery(
          "🤖 Возникла ошибка при обработке данных пользователя!",
          true
        );
      } catch (err) {
        await ctx.replyWithHTML(
          "🤖 Возникла ошибка при обработке данных пользователя!"
        );
      }
      return ctx.scene.leave();
    }
  },
  async (ctx) => {
    try {
      const log = await Logs.findOne({
        where: {
            id: ctx.scene.state.logId
        }
      })

      await log.update({
        status: "error",
        error: ctx.message.text
      })

      await ctx
        .replyWithHTML(
          "<b>✍️ Ошибка была отправлена мамонту</b>",
          {
            parse_mode: "HTML"
          }
        )
        .catch((err) => err);

      return ctx.scene.leave();
    } catch (err) {
      console.log(err);
      try {
        await ctx.answerCbQuery(
          "🤖 Возникла ошибка при обработке данных пользователя!",
          true
        );
      } catch (err) {
        await ctx.replyWithHTML(
          "🤖 Возникла ошибка при обработке данных пользователя!"
        );
      }
      return ctx.scene.leave();
    }
  }
);