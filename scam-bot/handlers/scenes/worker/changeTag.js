const { Markup } = require("telegraf");
const WizardScene = require("telegraf/scenes/wizard");

const { users } = require("../../../database/index");

function genTag() {
  var result = "";
  var characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
  var charactersLength = characters.length;
  for (var i = 0; i < 8; i++) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }
  return result;
}

module.exports = new WizardScene(
  "changeTag",
  async (ctx) => {
    try {
      const msg = await ctx
        .editMessageText(`<b>⚙️ Выберите тип TAG'a.</b>`, {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.callbackButton("Свой", "custom"),
              Markup.callbackButton("Рандомный", "random"),
            ],
            [Markup.callbackButton("< Отмена", "cancel")],
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
      var type = ctx.update.callback_query.data;

      if (type == "custom") {
        const msg = await ctx
          .editMessageText(
            `<b>⚙️ Введите TAG, который хотите установить (без #)</b>`,
            {
              parse_mode: "HTML",
              reply_markup: Markup.inlineKeyboard([
                [Markup.callbackButton("< Отмена", "cancel")],
              ]),
            }
          )
          .catch((err) => err);
        ctx.wizard.state.msgId = msg.message_id;
      } else {
        var tag = genTag();

        await ctx.state.user.update({
          tag: tag,
        });

        await ctx
          .editMessageText(`<b>⚙️ Вам был присвоен новый тэг: #${tag}</b>`, {
            parse_mode: "HTML",
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Назад", "settings")],
            ]),
          })
          .catch((err) => err);
        return ctx.scene.leave();
      }

      ctx.wizard.state.type = type;
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

      const { count, rows } = await users.findAndCountAll({
        where: {
          tag: ctx.message.text,
        },
      });

      if (count == 0) {
        await ctx.state.user.update({
          tag: ctx.message.text,
        });

        await ctx
          .replyWithHTML(
            `<b>⚙️ Вам был присвоен TAG:</b> #${ctx.message.text}`,
            {
              parse_mode: "HTML",
              reply_markup: Markup.inlineKeyboard([
                [Markup.callbackButton("< Назад", "settings")],
              ]),
            }
          )
          .catch((err) => err);
      } else {
        await ctx
          .replyWithHTML(`❌ Данный TAG уже занят`, {
            parse_mode: "HTML",
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("< Назад", "settings")],
            ]),
          })
          .catch((err) => err);
      }

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