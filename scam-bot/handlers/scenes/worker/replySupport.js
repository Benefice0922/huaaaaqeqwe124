const { Markup } = require("telegraf");
const WizardScene = require("telegraf/scenes/wizard");

const { Supports } = require("../../../database/index");

module.exports = new WizardScene(
  "replySupport",
  async (ctx) => {
    try {
      const msg = await ctx
        .replyWithHTML(
          `<b>✍️ Введите сообщение, которое хотите отправить в ТП</b>`,
          {
            parse_mode: "HTML",
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Отмена", "cancel")],
            ]),
          }
        )
        .catch((err) => err);
      ctx.wizard.state.itemId = ctx.match[1];
      ctx.wizard.state.msgId = msg.message_id;
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
      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      await Supports.create({
        itemId: ctx.wizard.state.itemId,
        text: ctx.message.text,
        who: "Support",
      });

      await ctx
        .replyWithHTML("<b>📩 Сообщение было отправлено!</b>", {
          parse_mode: "HTML",
        })
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