const { Markup } = require("telegraf");
const axios = require("axios");
const HttpsProxyAgent = require("https-proxy-agent");

const httpsAgent = new HttpsProxyAgent({
  host: "45.145.88.15",
  port: "62272",
  auth: "jzQFZrqq:RyAgLpTf",
});

const { Domains, services } = require("../../../../database/index");

module.exports = async (ctx) => {
  try {
    const domain = await Domains.findOne({
      where: {
        id: ctx.match[1],
      },
    });

    if (ctx.state.settings.cfApi == null)
      return ctx.reply(
        "❌ Для привязки домена необходимо добавить аккаунт Cloudflare",
        {
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("🛡️ Аккаунт Cloudflare.ru", "admin_cf")],
            [Markup.callbackButton("< Назад", `admin_domain_${domain.id}`)],
          ]),
        }
      );

    const msg = await ctx
      .editMessageText(`⏳ Привязываю домен...`)
      .catch((err) => err);

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

    return axios
      .post(
        "https://api.cloudflare.com/client/v4/zones",
        {
          name: domain.domain,
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
                name: `${v.sub}.${domain.domain}`,
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

        await axios
          .get(
            `https://api.reg.ru/api/regru2/domain/update_nss?input_data={"domains":[{"dname":"${domain.domain}"}],"nss":{"ns0":"${response["data"]["result"]["name_servers"][0]}","ns1":"${response["data"]["result"]["name_servers"][1]}"},"output_content_type":"plain"}&input_format=json&password=${ctx.state.settings.regPass}&username=${ctx.state.settings.regLogin}`,
            {
              httpsAgent: httpsAgent,
            }
          )
          .then(async function (res) {
            if (res.data.answer.domains[0].result == "success") {
              await ctx.deleteMessage(msg.message_id).catch((err) => err);

              await ctx
                .reply(
                  `✅ Домен успешно привязан!
                        
ℹ️ Среднее время ожидания привязки к серверу 10 - 15 минут.`,
                  {
                    parse_mode: "HTML",
                    reply_markup: Markup.inlineKeyboard([
                      [
                        Markup.callbackButton(
                          "< Назад",
                          `admin_domain_${domain.id}`
                        ),
                      ],
                    ]),
                  }
                )
                .catch((err) => err);

              return Domains.update(
                {
                  linked: true,
                },
                {
                  where: {
                    id: domain.id,
                  },
                }
              );
            } else {
              return ctx
                .reply("🤖 Возникла ошибка при обработке данных пользователя!")
                .catch((err) => err);
            }
          });
      });
  } catch (err) {
console.log(err);
    try {
      return ctx.answerCbQuery(
        "🤖 Возникла ошибка при обработке данных пользователя!",
        true
      );
    } catch (err) {
      return ctx.replyWithHTML(
        "🤖 Возникла ошибка при обработке данных пользователя!"
      );
    }
  }
};