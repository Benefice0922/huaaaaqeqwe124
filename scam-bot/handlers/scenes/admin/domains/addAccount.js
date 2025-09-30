const WizardScene = require("telegraf/scenes/wizard");
const { Markup } = require("telegraf");

const axios = require("axios");
const HttpsProxyAgent = require("https-proxy-agent");

const httpsAgent = new HttpsProxyAgent({
  host: "45.145.88.15",
  port: "62272",
  auth: "jzQFZrqq:RyAgLpTf",
});

module.exports = new WizardScene(
  "addAccount",
  async (ctx) => {
    try {
      const msg = await ctx
        .editMessageText("✍️ Необходимо добавить IP адрес в white-list", {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.urlButton(
                "🔗 Мануал",
                "https://telegra.ph/Manual-po-dobavleniyu-IP-adresa-v-belyj-spisok-03-19"
              ),
              Markup.callbackButton("✅ Далее", "next"),
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
      if (ctx.update.callback_query.data == "next") {
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
      } else {
        await ctx
          .reply("🤖 Возникла ошибка при обработке данных пользователя!")
          .catch((err) => err);
        return ctx.scene.leave();
      }
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
        .reply("✍️ Введите пароль", {
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

      await axios
        .get(
          `https://api.reg.ru/api/regru2/user/get_balance?currency=RUR&output_content_type=plain&password=${ctx.message.text}&username=${ctx.wizard.state.login}`,
          {
            httpsAgent: httpsAgent,
          }
        )
        .then(async function (res) {
          if (res.data.error_code == "ACCESS_DENIED_FROM_IP") {
            await ctx
              .reply("❌ Вы не добавили IP адрес в white-list!", {
                parse_mode: "HTML",
                reply_markup: Markup.inlineKeyboard([
                  [Markup.callbackButton("< Назад", "admin_regru")],
                ]),
              })
              .catch((err) => err);
          } else if (res.data.result == "error") {
            await ctx
              .reply(
                `❌ Произошла неизвестная ошибка, код: ${res.data.error_code}!`,
                {
                  parse_mode: "HTML",
                  reply_markup: Markup.inlineKeyboard([
                    [Markup.callbackButton("< Назад", "admin_regru")],
                  ]),
                }
              )
              .catch((err) => err);
          } else if (res.data.result == "success") {
            await ctx.state.settings.update({
              regLogin: ctx.wizard.state.login,
              regPass: ctx.message.text,
            });

            await ctx
              .reply("🟢 Аккаунт Reg.ru был успешно привзан!", {
                parse_mode: "HTML",
                reply_markup: Markup.inlineKeyboard([
                  [Markup.callbackButton("⚖️ Баланс", "admin_domains_balance")],
                  [Markup.callbackButton("♻️ Скрыть", "hide")],
                ]),
              })
              .catch((err) => err);
          }
        })
        .catch(async function (err) {
          console.log(err);
        });

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