const { Markup } = require("telegraf");
const WizardScene = require("telegraf/scenes/wizard");

const { items, services } = require("../../../../../database/index");

const parser = require("../../../../functions/createParser");

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
  "create_ebay1_de",
  async (ctx) => {
    try {
      ctx.wizard.state.service = ctx.match[1];

      await ctx
        .editMessageText("🇩🇪 <b>Выберите тип создания ссылки</b>", {
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
  async (ctx) => {
    try {
      ctx.wizard.state.type = ctx.update.callback_query.data;

      if (ctx.update.callback_query.data == "main") {
        const msg = await ctx
          .editMessageText("🇩🇪 Введите название товара", {
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Отменить", "cancel")],
            ]),
          })
          .catch((err) => err);

        ctx.wizard.state.msgId = msg.message_id;
      } else {
        const msg = await ctx
          .editMessageText("🇩🇪 Введите ссылку на товар", {
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
  async (ctx) => {
    try {
      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      if (ctx.wizard.state.type == "main") {
        ctx.wizard.state.title = ctx.message.text;

        const msg = await ctx
          .replyWithHTML("🇩🇪 Введите стоимость товара (только число)", {
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Отменить", "cancel")],
            ]),
          })
          .catch((err) => err);

        ctx.wizard.state.msgId = msg.message_id;
        return ctx.wizard.next();
      } else {
        let url;
        try {
          url = new URL(ctx.message.text);
        } catch (err) {
          await ctx
            .replyWithHTML("❌ Введите валидную ссылку")
            .catch((err) => err);
          return ctx.wizard.prevStep();
        }
        if (url.host == "ebay-kleinanzeigen.de") {
          url.host = "www.ebay-kleinanzeigen.de";
        }

        const service = await services.findOne({
          where: {
            code: ctx.wizard.state.service,
          },
        });

        const info = await parser(ctx.wizard.state.service, ctx.message.text);

        const item = await items.create({
          id: genId(),
          workerId: ctx.from.id,
          title: info.title,
          photo: info.photo,
          price: info.price,
          currency: service.currency,
          serviceCode: service.code,
          status: service.status,
        });

        await ctx
          .replyWithPhoto(
            { url: info.photo },
            {
              caption: `🗂️ <b>Текущий раздел:</b>
╰ 🇩🇪 Объявления -> ${service.title} ${service.status}.0

╭ 🧊 <b>Название:</b> ${info.title}
╰ 🧊 <b>Цена:</b> ${info.price}

╭ 🖼️ <a href="${info.photo}">Изображение</a>
╰ 🏠 <a href="https://${service.domain}/pay/order/${item.id}">Ваше объявление</a>`,
              parse_mode: "HTML",
              reply_markup: Markup.inlineKeyboard([
                [
                  Markup.urlButton(
                    "🔗 Перейти",
                    `https://${service.domain}/pay/order/${item.id}`
                  ),
                ],
                [
                  Markup.callbackButton("🖊️ Цена", `changePrice_${item.id}`),
                  // Markup.callbackButton("📱 SMS", `sendSms`),
                ],
                [Markup.callbackButton("< В меню", `menu`)],
              ]),
            }
          )
          .catch((err) => err);

        return ctx.scene.leave();
      }
    } catch (err) {
      console.log(err);
      return ctx.scene.leave();
    }
  },
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
            "🇩🇪 Введите ссылку на изображение (используйте @imgur_linkbot)",
            {
              reply_markup: Markup.inlineKeyboard([
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
  async (ctx) => {
    try {
      ctx.wizard.state.photo = ctx.message.text;

      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      const msg = await ctx
        .replyWithHTML("🇩🇪 Введите стоимость доставки", {
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
  async (ctx) => {
    try {
      ctx.wizard.state.deliveryPrice = ctx.message.text;

      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      if (isNaN(parseFloat(ctx.message.text))) {
        await ctx
          .replyWithHTML("❗️ Вы ввели не число, создание ссылки отменено", {
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< В меню", "menu")],
            ]),
          })
          .catch((err) => err);
      } else {
        const service = await services.findOne({
          where: {
            code: ctx.wizard.state.service,
          },
        });

        const item = await items.create({
          id: genId(),
          workerId: ctx.from.id,
          title: ctx.wizard.state.title,
          photo: ctx.wizard.state.photo,
          price: ctx.wizard.state.price,
          currency: service.currency,
          serviceCode: service.code,
          status: service.status,
        });

        await ctx
          .replyWithPhoto(
            { url: ctx.wizard.state.photo },
            {
              caption: `🗂️ <b>Текущий раздел:</b>
╰ 🇩🇪 Объявления -> ${service.title} ${service.status}.0

╭ 🧊 <b>Название:</b> ${ctx.wizard.state.title}
╰ 🧊 <b>Цена:</b> € ${parseInt(ctx.wizard.state.price)}

╭ 🖼️ <a href="${ctx.wizard.state.photo}">Изображение</a>
╰ 🏠 <a href="https://${service.domain}/pay/order/${item.id}">Ваше объявление</a>`,
              parse_mode: "HTML",
              reply_markup: Markup.inlineKeyboard([
                [
                  Markup.urlButton(
                    "🔗 Перейти",
                    `https://${service.domain}/pay/order/${item.id}`
                  ),
                ],
                [
                  Markup.callbackButton("🖊️ Цена", `changePrice_${item.id}`),
                  // Markup.callbackButton("📱 SMS", `sendSms`),
                ],
                [Markup.callbackButton("< В меню", `menu`)],
              ]),
            }
          )
          .catch((err) => err);
      }

      return ctx.scene.leave();
    } catch (err) {
      console.log(err);
      return ctx.scene.leave();
    }
  }
);