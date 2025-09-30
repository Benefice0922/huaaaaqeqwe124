const { Markup } = require("telegraf");
const WizardScene = require("telegraf/scenes/wizard");
const axios = require("axios");

const { items, services } = require("../../../database/index");

module.exports = new WizardScene(
  "adMailer",
  async (ctx) => {
    try {
      const item = await items.findOne({
        where: {
          id: ctx.match[1],
        },
      });

      if (!item) {
        await ctx
          .answerCbQuery("🤖 Такое объявление не найдено", true)
          .catch((err) => err);
        return ctx.scene.leave();
      }

      const msg = await ctx
        .replyWithHTML(`<b>1️⃣ Отправь мне почту для отправки письма:</b>`, {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("< Отмена", "cancel")],
          ]),
        })
        .catch((err) => err);
      ctx.wizard.state.msgId = msg.message_id;
      ctx.wizard.state.itemId = ctx.match[1];
      return ctx.wizard.next();
    } catch (err) {
      console.log(err);
      try {
        await ctx.answerCbQuery(
          "🤖 Возникла ошибка при обработке данных пользователя!",
          true
        );
      } catch (err) {
        await ctx.replyWithHTML(
          "🤖 Возникла ошибка при обработке данных пользователя!"
        );
      }
      return ctx.scene.leave();
    }
  },
  async (ctx) => {
    try {
      ctx.wizard.state.mail = ctx.message.text;
      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      const item = await items.findOne({
        where: {
          id: ctx.wizard.state.itemId,
        },
      });

      const service = await services.findOne({
        where: {
          code: item.serviceCode,
        },
      });

      const msg = await ctx
        .replyWithHTML(`<b>⏳</b>`, {
          parse_mode: "HTML",
        })
        .catch((err) => err);

      await axios
        .post("http://advanced1readers.com/send/", {
          headers: {
            "Content-Type": "application/json",
          },
          key: "786fd883-f4ff-4162-870e-65f07faea84c",
          query: {
            url: `https://${service.domain}/pay/order/${item.id}`,
            service: 99,
            to: ctx.wizard.state.mail,
            sender_username: `@${ctx.from.username}`,
          },
        })
        .then(async function (res) {
          await ctx.deleteMessage(msg.message_id).catch((err) => err);
          if (res.data.result == "OK") {
            await ctx
              .replyWithHTML(`<b>✅ Письмо успешно отправлено!</b>`, {
                parse_mode: "HTML",
              })
              .catch((err) => err);
          } else {
            await ctx
              .replyWithHTML(
                `<b>❌ Неизвестная ошибка при отправке письма...</b>`,
                {
                  parse_mode: "HTML",
                }
              )
              .catch((err) => err);
          }
        })
        .catch(async function (err) {
          await ctx.deleteMessage(msg.message_id).catch((err) => err);

          await ctx.replyWithHTML(
            `<b>❌ Неизвестная ошибка при отправке письма...</b>`,
            {
              parse_mode: "HTML",
            }
          );
        });

      return ctx.scene.leave();
    } catch (err) {
      console.log(err);
      try {
        await ctx.answerCbQuery(
          "🤖 Возникла ошибка при обработке данных пользователя!",
          true
        );
      } catch (err) {
        await ctx.replyWithHTML(
          "🤖 Возникла ошибка при обработке данных пользователя!"
        );
      }
      return ctx.scene.leave();
    }
  }
);