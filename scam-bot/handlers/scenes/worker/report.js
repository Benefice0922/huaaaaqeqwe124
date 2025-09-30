const { Markup } = require("telegraf");
const WizardScene = require("telegraf/scenes/wizard");

module.exports = new WizardScene(
  "report",
  async (ctx) => {
    try {
      const msg = await ctx
        .editMessageText(`<b>✍️ Опишите проблему...</b>`, {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
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
      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      await ctx.telegram.sendMessage(
        ctx.state.settings.requestChatId,
        `⚠️ <b>Новая жалоба!
        
✍️ Описание проблемы:</b> <code>${ctx.message.text}</code>`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.callbackButton(
                "🤷🏼‍♂️ Заблокировать пользователя",
                `user_ban_${ctx.from.id}`
              ),
            ],
          ]),
        }
      );

      await ctx
        .replyWithHTML(
          "<b>✍️ Запрос был успешно передан администрации. Ожидайте, пока его рассмотрят.</b>",
          {
            parse_mode: "HTML",
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Назад", "menu")],
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