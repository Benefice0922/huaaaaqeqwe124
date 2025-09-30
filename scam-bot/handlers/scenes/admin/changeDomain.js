const WizardScene = require("telegraf/scenes/wizard");
const { Markup } = require("telegraf");
const { services, countries } = require("../../../database/index");

const chunk = require("chunk")

module.exports = new WizardScene(
  "changeDomain",
  async (ctx) => {
    try {
      const Countries = await countries
        .findAll({
          where: {
            work: true,
          },
        })
        .catch((err) => err);

      var buttons = chunk(
        Countries.map((v) => Markup.callbackButton(v.title, v.id))
      );

      if (buttons.length < 1) {
        buttons = [[Markup.callbackButton("Стран нет :(", "none")]];
      }

      await ctx
        .editMessageText("<b>1️⃣ Выбери страну для смены домена:</b>", {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            ...buttons,
            [Markup.callbackButton("< Отмена", "cancel")],
          ]),
        })
        .catch((err) => err);
      return ctx.wizard.next();
    } catch (err) {
        console.log(err)
      await ctx
        .reply("🤖 Возникла ошибка при обработке данных пользователя!")
        .catch((err) => err);
      return ctx.scene.leave();
    }
  },
  async (ctx) => {
    try {
      const Services = await services
        .findAll({
          where: {
            work: true,
            id: ctx.update.callback_query.data,
          },
        })
        .catch((err) => err);

      var buttons = chunk(
        Services.map((v) =>
          Markup.callbackButton(`${v.title} ${v.status}.0`, v.code)
        )
      );

      if (buttons.length < 1) {
        buttons = [[Markup.callbackButton("Сервисов нет :(", "none")]];
      }

      await ctx
        .editMessageText("<b>2️⃣ Выбери сервис для смены домена:</b>", {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            ...buttons,
            [Markup.callbackButton("< Отмена", "cancel")],
          ]),
        })
        .catch((err) => err);
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
      ctx.wizard.state.serviceCode = ctx.update.callback_query.data;

      const msg = await ctx
        .editMessageText("<b>3️⃣ Введи новый домен для сервиса:</b>", {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("< Отмена", "cancel")],
          ]),
        })
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

      const service = await services.findOne({
        where: {
          code: ctx.wizard.state.serviceCode,
        },
      });

      await service.update({
        domain: ctx.message.text,
      });

      await ctx
        .replyWithHTML("<b>✅ Домен успешно сменен</b>", {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("< Назад", "menu")],
          ]),
        })
        .catch((err) => err);
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
