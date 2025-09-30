const { Markup } = require("telegraf");
const WizardScene = require("telegraf/scenes/wizard");

const { Mentors } = require("../../../database/index");

module.exports = new WizardScene(
  "sendMentorReq",
  async (ctx) => {
    try {
      const mentor = await Mentors.findOne({
        where: {
          workerId: ctx.from.id,
        },
      });

      if (!mentor) {
        const msg = await ctx
          .editMessageText(
            `<b>🧑‍🏫 Введите краткую информацию о себе.
💬 P.S:</b> По этой информации администрация будет судить - брать вас в наставники или нет.`,
            {
              parse_mode: "HTML",
              reply_markup: Markup.inlineKeyboard([
                [Markup.callbackButton("< Отмена", "cancel")],
              ]),
            }
          )
          .catch((err) => err);
        ctx.wizard.state.msgId = msg.message_id;
        return ctx.wizard.next();
      } else if (mentor.status == true) {
        await ctx.editMessageText("⚠️ <b>Ты уже наставник!</b>", {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("< Назад", "mentors")],
          ]),
        });
        return ctx.scene.leave();
      } else if (mentor.status == false) {
        await ctx.editMessageText(
          "⚠️ <b>Твоя заявка находится на проверке...</b>",
          {
            parse_mode: "HTML",
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Назад", "mentors")],
            ]),
          }
        );
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
      await ctx.deleteMessage().catch((err) => err);
      await ctx.deleteMessage(ctx.wizard.state.msgId).catch((err) => err);

      const mentor = await Mentors.create({
        workerId: ctx.from.id,
        username: ctx.from.username,
        about: ctx.message.text,
        percent: ctx.state.settings.mentorPercent
      });

      await ctx.telegram.sendMessage(
        ctx.state.settings.requestChatId,
        `🧑‍🏫 Заявка на наставника
        
<b>💁🏼‍♂️ Подал: @${ctx.from.username} |</b> <code>${ctx.from.id}</code>

<b>💬 О нем:</b> <b>${ctx.message.text}</b>`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.callbackButton("✅ Принять", `mentor_accept_${mentor.id}`),
              Markup.callbackButton(
                "❌ Отклонить",
                `mentor_decline_${mentor.id}`
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

      await ctx
        .replyWithHTML(
          "<b>⚡️ Ваша заявка была отправлена, ожидайте ответа!</b>",
          {
            parse_mode: "HTML",
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Назад", "mentors")],
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