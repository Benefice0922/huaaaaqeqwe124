const WizardScene = require("telegraf/scenes/wizard");
const { Markup } = require("telegraf");

module.exports = new WizardScene(
  "addCf",
  async (ctx) => {
    try {
        const msg = await ctx
          .editMessageText("✍️ Введите логин (почта)", {
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
      ctx.wizard.state.login = ctx.message.text;

      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      const msg = await ctx
        .reply("✍️ Введите ID аккаунта", {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [
                Markup.urlButton(
                  "🔗 Мануал",
                  "https://telegra.ph/Kak-poluchit-ID-akkaunta-cloudflarecom-03-20"
                ),
              ],
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
      ctx.wizard.state.cfId = ctx.message.text;

      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      const msg = await ctx
        .reply("✍️ Введите General API-Key от аккаунта", {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [
                Markup.urlButton(
                  "🔗 Мануал",
                  "https://telegra.ph/Kak-poluchit-General-API-Key-cloudflarecom-03-20"
                ),
              ],
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

      await ctx.state.settings.update({
        cfMail: ctx.wizard.state.login,
        cfId: ctx.wizard.state.cfId,
        cfApi: ctx.message.text,
      });

      await ctx
        .reply("🟢 Аккаунт Cloudflare.com был успешно привзан!", {
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
  },
);