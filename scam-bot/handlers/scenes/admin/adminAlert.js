const WizardScene = require("telegraf/scenes/wizard");
const { Markup } = require("telegraf");
const { users } = require("../../../database/index");

module.exports = new WizardScene(
  "adminAlert",
  async (ctx) => {
    try {
      const msg = await ctx
        .editMessageText("<b>1️⃣ Введите текст для рассылки</b>", {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("< Отмена", "cancel")],
          ]),
        })
        .catch((err) => err);
      ctx.wizard.state.msgId = msg.message_id;
      return ctx.wizard.next();
    } catch (err) {
      await ctx
        .reply("🤖 Возникла ошибка при обработке данных пользователя!")
        .catch((err) => err);
      return ctx.scene.leave();
    }
  },
  async (ctx) => {
    try {
      // Получаем только пользователей с включенными уведомлениями
const Users = await users.findAndCountAll({
  where: {
    botNotifications: true  // Только пользователи с включенной рассылкой
  }
});

      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      await ctx
        .replyWithHTML("<b>✅ Рассылка запускается...</b>", {
          parse_mode: "HTML",
        })
        .catch((err) => err);

      await Promise.allSettled(
        Users.rows.map(
          async (v) =>
            await ctx.telegram
              .sendMessage(v.id, ctx.message.text, {
                parse_mode: "HTML",
                reply_markup: Markup.inlineKeyboard([
                  [Markup.callbackButton("♻️ Скрыть", "hide")],
                ]),
              })
              .catch((err) => err)
        )
      ).catch((err) => err);

      return ctx.scene.leave();
    } catch (err) {
      console.log(err);
      await ctx
        .reply("🤖 Возникла ошибка при обработке данных пользователя!")
        .catch((err) => err);
      return ctx.scene.leave();
    }
  }
);