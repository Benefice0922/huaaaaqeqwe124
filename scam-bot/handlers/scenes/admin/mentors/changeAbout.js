const WizardScene = require("telegraf/scenes/wizard");
const { Markup } = require("telegraf");

const { Mentors } = require("../../../../database/index");

module.exports = new WizardScene(
  "mentorChangeAbout",
  async (ctx) => {
    try {
      const msg = await ctx
        .editMessageText("✍️ Введите новое описание для наставника", {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("< Отмена", "cancel")],
          ]),
        })
        .catch((err) => err);

      ctx.wizard.state.msgId = msg.message_id;
      ctx.wizard.state.mentorId = ctx.match[1];

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

      await Mentors.update(
        {
          about: ctx.message.text,
        },
        {
          where: {
            id: ctx.wizard.state.mentorId,
          },
        }
      );

      await ctx
        .reply("🟢 Описание было успешно изменен!", {
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