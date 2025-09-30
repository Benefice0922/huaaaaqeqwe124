const { Markup } = require("telegraf");

const { users, Profits } = require("../../../../database/index");

module.exports = async (ctx) => {
  try {
    const username = ctx.match[1];
    const user = await users.findOne({ where: { username: username } });

    if (!user)
      return ctx.reply("❌ Пользователь не найден.", {
        reply_markup: Markup.inlineKeyboard([
          [Markup.callbackButton("♻️ Скрыть", "hide")],
        ]),
      });

    if (parseInt(user.profitSum) < 0) {
      await user.update({
        profitSum: 0,
      });
    }

    const profitsSum = parseFloat(
      await Profits.sum("eurAmount", {
        where: { workerId: user.id },
      })
    );

    await ctx.deleteMessage().catch((err) => err);

    await ctx
      .replyWithHTML(
        `<b>🗂️ Текущий раздел:</b>
╰ 👨🏻‍💻 Управление воркером

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

╭ 👤 <b>${
          user.admin == true
            ? "Администратор"
            : user.vbiver == true
            ? "Вбивер"
            : "Воркер"
        }:</b> @${user.username}
├ 💰 <b>Всего заработал:</b> € ${
          isNaN(profitsSum)
            ? "0"
            : ((profitsSum / 100) * user.percent).toFixed(2)
        }
├ 🏦 <b>Кошелек для выплаты:</b> ${
          user.wallet == null
            ? "Не установлен"
            : `<code>${user.wallet.split("&")[1]}</code> (${
                user.wallet.split("&")[0]
              })`
        }
╰ #️⃣ <b>TAG:</b> <code>#${user.tag}</code>

├ ⚖️ <b>Процентная ставка:</b> ${ctx.state.user.percent}%`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.callbackButton(
                `${user.banned == true ? "🟢 Разбанить" : "🔴 Забанить"}`,
                `user_${user.banned == true ? "unban" : "ban"}_${user.id}`
              ),
              Markup.callbackButton(
                "🛠 Изменить статус",
                `admin_userStatus_${user.id}`
              ),
            ],
            [
              Markup.callbackButton(
                "💰 Профиты",
                `admin_profitsUser_${user.id}`
              ),
              Markup.callbackButton(
                "🔁 Изменить процент",
                `admin_changePercent_${user.id}`
              ),
            ],
            [Markup.callbackButton("♻️ Скрыть", "hide")],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
console.log(err);
    try {
      return ctx.answerCbQuery(
        "🤖 Возникла ошибка при обработке данных пользователя!",
        true
      );
    } catch (err) {
      return ctx.replyWithHTML(
        "🤖 Возникла ошибка при обработке данных пользователя!"
      );
    }
  }
};