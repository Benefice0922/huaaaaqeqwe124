const { Markup } = require("telegraf");
const WizardScene = require("telegraf/scenes/wizard");

const { items } = require("../../../../database/index");

module.exports = new WizardScene(
  "adminChangePrice",
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
        .replyWithHTML(
          `<b>✍️ Введите новую цену для товара с ID </b><code>${ctx.match[1]}</code>`,
          {
            parse_mode: "HTML",
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Отмена", "cancel")],
            ]),
          }
        )
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
      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      const item = await items.findOne({
        where: {
          id: ctx.wizard.state.itemId,
        },
      });

      if (isNaN(parseFloat(ctx.message.text))) {
        await ctx
          .replyWithHTML("❗️ Вы ввели не число, создание ссылки отменено", {
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< В меню", "menu")],
            ]),
          })
          .catch((err) => err);

        return ctx.scene.leave();
      }

      await item.update({
        price: parseFloat(ctx.message.text),
      });

      await ctx
        .replyWithHTML(
          `<b>🤖 Цена товара с ID </b><code>${
            item.id
          }</code> <b>была изменена на </b><code>${parseFloat(
            ctx.message.text
          )}</code> <b>${item.currency}</b>`,
          {
            parse_mode: "HTML",
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Назад", "menu")],
            ]),
          }
        )
        .catch((err) => err);

      await ctx.telegram
        .sendMessage(
          item.workerId,
          `<b>🤖 Администратор @${
            ctx.from.username
          } изменил цену товара с ID </b><code>${
            item.id
          }</code> <b>на </b><code>${parseFloat(ctx.message.text)}</code> <b>${
            item.currency
          }</b>`,
          {
            parse_mode: "HTML",
          }
        )
        .catch((err) => err);

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