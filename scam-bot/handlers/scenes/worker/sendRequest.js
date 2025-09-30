const { Markup } = require("telegraf");
const WizardScene = require("telegraf/scenes/wizard");

const { Requests } = require("../../../database/index");

module.exports = new WizardScene(
  "sendRequest",
  async (ctx) => {
    try {
      const req = await Requests.findOne({
        where: {
          workerId: ctx.from.id,
        },
      });

      if (!req) {
        const msg = await ctx
          .editMessageText(
            "<b>1️⃣ Укажите ваши предыдущие места работы (</b>названия команд<b>)</b>",
            {
              parse_mode: "HTML",
              reply_markup: Markup.inlineKeyboard([
                [Markup.callbackButton("< Отмена", "requestCancel")],
              ]),
            }
          )
          .catch((err) => err);
        ctx.wizard.state.msgId = msg.message_id;
        return ctx.wizard.next();
      } else {
        await ctx
          .editMessageText(
            "<b>⏳ Твоя заявка находится в обработке...</b>",
            {
              parse_mode: "HTML"
            }
          )
          .catch((err) => err);
        return ctx.scene.leave();
      }
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
      ctx.wizard.state.lastWork = ctx.message.text;
      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      const msg = await ctx
        .replyWithHTML("<b>2️⃣ Причина ухода оттуда</b>", {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("< Отмена", "requestCancel")],
          ]),
        })
        .catch((err) => err);

      ctx.wizard.state.msgId = msg.message_id;

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
      ctx.wizard.state.reasonLeave = ctx.message.text;

      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);
      const msg = await ctx
        .replyWithHTML(
          "<b>3️⃣ Скрины профитов (</b>ссылки на изображения<b>)</b>",
          {
            parse_mode: "HTML",
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Отмена", "requestCancel")],
            ]),
          }
        )
        .catch((err) => err);

      ctx.wizard.state.msgId = msg.message_id;
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

      await ctx.telegram.sendMessage(
        ctx.scene.state.requestChatId,
        `⚡️ Новая заявка на борту!
        
<b>💁🏼‍♂️ Подал: @${ctx.from.username} |</b> <code>${ctx.from.id}</code>

<b>1️⃣ Предыдущие места работы:</b> <b>${ctx.wizard.state.lastWork}</b>
<b>2️⃣ Причина ухода:</b> <b>${ctx.wizard.state.reasonLeave}</b>
<b>3️⃣ Скрины профитов:</b> <b>${ctx.message.text}</b>`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.callbackButton(
                "✅ Принять",
                `request_accept_${ctx.from.id}`
              ),
              Markup.callbackButton(
                "❌ Отклонить",
                `request_decline_${ctx.from.id}`
              ),
            ],
            [
              Markup.callbackButton(
                "🤷🏼‍♂️ Заблокировать",
                `user_ban_${ctx.from.id}`
              ),
            ],
          ]),
        }
      );

      await Requests.create({
        workerId: ctx.from.id,
        question1: ctx.wizard.state.lastWork,
        question2: ctx.wizard.state.reasonLeave,
        question3: ctx.message.text,
      });

      await ctx
        .replyWithHTML(
          "<b>⚡️ Ваша заявка была отправлена, ожидайте ответа!</b>",
          {
            parse_mode: "HTML",
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("♻️ Скрыть", "hide")],
            ]),
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