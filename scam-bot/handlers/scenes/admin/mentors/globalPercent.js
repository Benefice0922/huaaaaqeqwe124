const WizardScene = require("telegraf/scenes/wizard");
const { Markup } = require("telegraf");

const { Mentors } = require("../../../../database/index");

module.exports = new WizardScene(
  "mentorPercent",
  async (ctx) => {
    try {
      const msg = await ctx
        .editMessageText("✍️ Введите новый процент для наставника", {
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
      await ctx
        .reply("🤖 Возникла ошибка при обработке данных пользователя!")
        .catch((err) => err);
      return ctx.scene.leave();
    }
  },
  async (ctx) => {
    try {
      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      if(isNaN(parseFloat(ctx.message.text))) {
        await ctx.replyWithHTML("❌ Введи число", {
            reply_markup: Markup.inlineKeyboard([
                [Markup.callbackButton("< Назад", `admin_mentors`)]
            ])
        })
        return ctx.scene.leave()
      }

      await ctx.state.settings.update({
        mentorPercent: ctx.message.text
      })

      await ctx
        .reply("🟢 Процент был успешно изменен!", {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("♻️ Скрыть", "hide")],
          ]),
        })
        .catch((err) => err);

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