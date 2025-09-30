const { Markup } = require("telegraf");
const WizardScene = require("telegraf/scenes/wizard");

module.exports = new WizardScene(
  "setSmartsupp",
  async (ctx) => {
    try {
      const msg = await ctx
        .editMessageText(
          `<b>⚙️ Введите API-Ключ от smartsupp, который хотите установить.
❕ Пример:</b> <code>d0b5e22bb2d23466bf41ffe5641018a9294dc98c</code>`,
          {
            parse_mode: "HTML",
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Отмена", "cancel")],
            ]),
          }
        )
        .catch((err) => err);
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

      await ctx.state.user.update({
        supportType: ctx.message.text,
      });

      await ctx
        .replyWithHTML(
          `<b>⚙️ Вам был присвоено ТП:</b> <code>Smartsupp</code>
❕ <b>Установленный ключ:</b> <code>${ctx.message.text}</code>`,
          {
            parse_mode: "HTML",
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Назад", "typeSupport")],
            ]),
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