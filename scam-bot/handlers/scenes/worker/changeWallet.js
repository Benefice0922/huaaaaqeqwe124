const { Markup } = require("telegraf");
const WizardScene = require("telegraf/scenes/wizard");

module.exports = new WizardScene(
  "changeWallet",
  async (ctx) => {
    try {
      const msg = await ctx
        .editMessageText(`<b>💳 Выберите криптовалютный кошелёк</b>`, {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.callbackButton("BTC", "btc"),
              Markup.callbackButton("ETH", "eth"),
            ],
            [Markup.callbackButton("USDT TRC-20", "usdt")],
            [Markup.callbackButton("< Отмена", "cancel")],
          ]),
        })
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
      var type = ctx.update.callback_query.data;

      const msg = await ctx
        .editMessageText(`<b>💳 Введите ваш ${type.toUpperCase()} адрес</b>`, {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("< Отмена", "cancel")],
          ]),
        })
        .catch((err) => err);

      ctx.wizard.state.type = type;
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
        wallet: `${ctx.wizard.state.type.toUpperCase()}&${ctx.message.text}`,
      });

      await ctx
        .replyWithHTML(
          `<b>💳 Ваш </b><code>${ctx.wizard.state.type.toUpperCase()}</code> <b>адрес был изменён на </b><code>${ctx.message.text}</code>`,
          {
            parse_mode: "HTML",
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Назад", "wallet")],
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