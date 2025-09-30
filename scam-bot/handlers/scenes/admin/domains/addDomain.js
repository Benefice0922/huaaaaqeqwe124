const WizardScene = require("telegraf/scenes/wizard");
const { Markup } = require("telegraf");
const axios = require("axios");
const HttpsProxyAgent = require("https-proxy-agent");

const { Domains } = require("../../../../database/index");

const httpsAgent = new HttpsProxyAgent({
  host: "45.145.88.15",
  port: "62272",
  auth: "jzQFZrqq:RyAgLpTf",
});

module.exports = new WizardScene(
  "addDomain",
  async (ctx) => {
    try {
      const msg = await ctx
        .editMessageText(
          `✍️ Введите домен, который хотите приобрести

Примеры доменов: de-classsifelds.shop / de-onlineclasssifelds.xyz / eu-onlinestore.com`,
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

      ctx.wizard.state.domain = ctx.message.text;

      const domainCount = await Domains.count({
        where: {
          domain: ctx.message.text,
        },
      });

      if (domainCount > 0) {
        await ctx
          .reply("❌ Такой домен уже добавлен в бота!", {
            parse_mode: "HTML",
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Назад", "admin_domains")],
            ]),
          })
          .catch((err) => err);
        return ctx.scene.leave();
      }

      const msg = await ctx
        .reply(`⏳ Проверяю свободен ли домен...`, {
          parse_mode: "HTML",
        })
        .catch((err) => err);

      ctx.wizard.state.msgId = msg.message_id;

      await axios
        .post(
          `https://api.reg.ru/api/regru2/domain/check?input_data={"domains":[{"dname":"${ctx.message.text}"}]}&input_format=json&password=test&username=test`,
          {
            httpsAgent: httpsAgent,
          }
        )
        .then(async function (res) {
          if (res.data.answer.domains[0].result == "Available") {
            await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

            const msg = await ctx
              .reply(`⏳ Домен свободен, узнаю цену...`, {
                parse_mode: "HTML",
              })
              .catch((err) => err);

            ctx.wizard.state.msgId = msg.message_id;

            await axios
              .get(
                `https://api.reg.ru/api/regru2/domain/get_prices?output_content_type=plain&password=${ctx.state.settings.regPass}&username=${ctx.state.settings.regLogin}`,
                {
                  httpsAgent: httpsAgent,
                }
              )
              .then(async function (res) {
                ctx.wizard.state.price =
                  res.data.answer.prices[
                    ctx.message.text.split(".")[1]
                  ].reg_price;

                await ctx
                  .deleteMessage(ctx.wizard.state.msgId)
                  .catch((err) => err);

                await ctx
                  .reply(
                    `💰 <b>Стоимость домена:</b> ${
                      res.data.answer.prices[ctx.message.text.split(".")[1]]
                        .reg_price
                    } ₽
                    
🔗 <b>Домен:</b> ${ctx.message.text} (${ctx.message.text.split(".")[1]})`,
                    {
                      parse_mode: "HTML",
                      reply_markup: Markup.inlineKeyboard([
                        [
                          Markup.callbackButton("Купить", "buy"),
                          Markup.callbackButton("Отменить", "cancel"),
                        ],
                      ]),
                    }
                  )
                  .catch((err) => err);

                return ctx.wizard.next();
              });
          } else {
            await ctx
              .reply(`❌ Домен занят, попробуй другой...`, {
                parse_mode: "HTML",
                reply_markup: Markup.inlineKeyboard([
                  [Markup.callbackButton("< Назад", "admin_domains")],
                ]),
              })
              .catch((err) => err);

            return ctx.scene.leave();
          }
        });
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
      if (ctx.update.callback_query.data == "buy") {
        await axios
          .get(
            `https://api.reg.ru/api/regru2/user/get_balance?currency=RUR&output_content_type=plain&password=${ctx.state.settings.regPass}&username=${ctx.state.settings.regLogin}`,
            {
              httpsAgent: httpsAgent,
            }
          )
          .then(async function (res) {
            ctx.wizard.state.balance = res.data.answer.prepay;

            if (
              parseInt(res.data.answer.prepay) >=
              parseInt(ctx.wizard.state.price)
            ) {
              const msg = await ctx
                .editMessageText(`⏳ Отправил запрос на покупку домена...`, {
                  parse_mode: "HTML",
                })
                .catch((err) => err);

              ctx.wizard.state.msgId = msg.message_id;

              await axios
                .get(
                  `https://api.reg.ru/api/regru2/domain/create?input_data={"contacts":{"country":"RU","a_addr":"Bolshoy sobachiy, 33","a_city":"Moscow","a_company":"Luntik, LLC","a_country_code":"RU","a_email":"${ctx.state.settings.regLogin}","a_first_name":"Ivan","a_last_name":"Ivanov","a_phone":"+79817655676","a_postcode":"101000","a_state":"Moscow","b_addr":"asdfasdfasdf asdfas asdf","b_city":"Moscow","b_company":"Luntik, LLC","b_country_code":"RU","b_first_name":"Ivan","b_last_name":"Ivanov","b_phone":"+79817655676","b_postcode":"101000","b_state":"Moscow","o_addr":"ssdfdsf sdfdsf","o_city":"Moscow","o_company":"Luntik, LLC","o_country_code":"RU","o_email":"${ctx.state.settings.regLogin}","o_phone":"+79817655676","o_postcode":"101000","o_state":"Moscow","t_addr":"sdfgsdfg sdfg","t_city":"Moscow","t_company":"Luntic OOC","t_country_code":"RU","t_email":"sdfsdaf@gmail.com","t_first_name":"Ivan","t_last_name":"Ivanov","t_phone":"+79817655676","t_postcode":"101000","t_state":"Moscow","country":"RU","country":"RU","country":"RU","country":"RU","country":"RU","country":"RU","country":"RU","country":"RU","country":"RU","country":"RU","country":"RU","b_email":"${ctx.state.settings.regLogin}","e_mail":"${ctx.state.settings.regLogin}","person_r_surname":"Рюрик","person_r_name":"Святослав","person_r_patronimic":"Владимирович","phone":"+79817655676","birth_date":"31.12.1999","descr":"Demo Site","person":"Ivanov Ivan Ivanovich","p_addr_zip":"101000","p_addr_area":"Ленина 12","p_addr_city":"г. Москва","p_addr_addr":"ул. Княжеска, д.1","p_addr_recipient":"Рюрику Святославу Владимировичу","passport_number":"22 44 668800","passport_place":"выдан по месту правления","passport_date":"23.12.2020"},"domains":[{"dname":"${ctx.wizard.state.domain}","srv_certificate":"free","srv_parking":"free"}],"nss":{"ns0":"ns1.reg.ru","ns1":"ns2.reg.ru"}}&input_format=json&output_content_type=plain&password=${ctx.state.settings.regPass}&username=${ctx.state.settings.regLogin}`,
                  {
                    httpsAgent: httpsAgent,
                  }
                )
                .then(async function (res) {
                  if (res.data.answer.pay_type == "nonexistent") {
                    await ctx
                      .deleteMessage(ctx.wizard.state.msgId)
                      .catch((err) => err);

                    await ctx
                      .reply(
                        `❌ На балансе недостаточно средств!

♻️ <b>Текущий баланс:</b> ${ctx.wizard.state.balance} ₽
💰 <b>Стоимость домена:</b> ${ctx.wizard.state.price} ₽`,
                        {
                          parse_mode: "HTML",
                          reply_markup: Markup.inlineKeyboard([
                            [Markup.callbackButton("< Назад", "admin_domains")],
                          ]),
                        }
                      )
                      .catch((err) => err);
                  } else if (
                    res.data.answer.pay_notes == "Amount successfully charged"
                  ) {
                    await ctx
                      .deleteMessage(ctx.wizard.state.msgId)
                      .catch((err) => err);

                    await Domains.create({
                      domain: ctx.wizard.state.domain,
                    });
                    await ctx
                      .reply(
                        `✅ Домен успешно куплен!
                      
ℹ️ Для продолжения нажми на кнопку ниже.`,
                        {
                          parse_mode: "HTML",
                          reply_markup: Markup.inlineKeyboard([
                            [
                              Markup.callbackButton(
                                "⚙️ Домены",
                                "admin_allDomains"
                              ),
                            ],
                            [Markup.callbackButton("< Назад", "admin_domains")],
                          ]),
                        }
                      )
                      .catch((err) => err);
                  } else {
                    await ctx
                      .reply(
                        "🤖 Возникла ошибка при обработке данных пользователя!"
                      )
                      .catch((err) => err);
                  }
                });
            } else {
              await ctx
                .reply(
                  `❌ На балансе недостаточно средств!
        
♻️ <b>Текущий баланс:</b> ${res.data.answer.prepay} ₽
💰 <b>Стоимость домена:</b> ${ctx.wizard.state.price} ₽`,
                  {
                    parse_mode: "HTML",
                    reply_markup: Markup.inlineKeyboard([
                      [Markup.callbackButton("< Назад", "admin_domains")],
                    ]),
                  }
                )
                .catch((err) => err);
            }
          });
      } else {
        await ctx
          .reply("🤖 Возникла ошибка при обработке данных пользователя!")
          .catch((err) => err);
      }
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