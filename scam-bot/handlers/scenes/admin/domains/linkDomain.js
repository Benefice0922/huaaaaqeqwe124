const WizardScene = require("telegraf/scenes/wizard");
const { Markup } = require("telegraf");
const axios = require("axios");

const { Domains, services } = require("../../../../database/index");

module.exports = new WizardScene(
  "linkDomain",
  async (ctx) => {
    try {
      const msg = await ctx
        .editMessageText("✍️ Введите домен который уже куплен", {
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

      var ns1 = "";
      var ns2 = "";

      let ip = await axios
        .get("https://api.ipify.org/?format=json")
        .then(function (response) {
          return response["data"]["ip"];
        })
        .catch(function (err) {
          return ctx
            .reply("🤖 Возникла ошибка при обработке данных пользователя!")
            .catch((err) => err);
        });

      const msg = await ctx.reply("⏳ Привязываю домен...").catch((err) => err);

      ctx.wizard.state.msgId = msg.message_id;

      await axios
        .post(
          "https://api.cloudflare.com/client/v4/zones",
          {
            name: ctx.message.text,
            jump_start: true,
            account: {
              id: ctx.state.settings.cfId,
            },
          },
          {
            headers: {
              "X-Auth-Email": ctx.state.settings.cfMail,
              "X-Auth-Key": ctx.state.settings.cfApi,
              "Content-Type": "application/json",
            },
          }
        )
        .then(async function (response) {
          ns1 = response["data"]["result"]["name_servers"][0];
          ns2 = response["data"]["result"]["name_servers"][1];

          const Services = await services.findAll();

          Services.map((v) =>
            axios
              .post(
                `https://api.cloudflare.com/client/v4/zones/${response["data"]["result"]["id"]}/dns_records`,
                {
                  type: "A",
                  name: `${v.sub}.${ctx.message.text}`,
                  content: ip,
                  ttl: 3600,
                  proxied: true,
                },
                {
                  headers: {
                    "X-Auth-Email": ctx.state.settings.cfMail,
                    "X-Auth-Key": ctx.state.settings.cfApi,
                    "Content-Type": "application/json",
                  },
                }
              )
              .then(async function (res) {})
              .catch(async function (err) {})
          );
          await ctx.deleteMessage(msg.message_id).catch((err) => err);

          await ctx
            .reply(
              `✅ Домен успешно привязан в Cloudflare!
                        
ℹ️ Измените DNS у купленного домена на следующие:

<code>${ns1}</code>
<code>${ns2}</code>`,
              {
                parse_mode: "HTML",
                reply_markup: Markup.inlineKeyboard([
                  [
                    Markup.callbackButton(
                      "< Назад",
                      `admin_domains`
                    ),
                  ],
                ]),
              }
            )
            .catch((err) => err);
        });

      await Domains.create({
        domain: ctx.message.text,
        linked: true,
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