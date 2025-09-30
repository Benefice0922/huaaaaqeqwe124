const { Markup } = require("telegraf");
const chunk = require("chunk");

const { Profits, users } = require("../../../../database/index");

module.exports = async (ctx) => {
  try {
    const worker = await users.findOne({
      where: {
        id: ctx.match[1],
      },
    });

    const profits = await Profits.findAll({
      where: {
        status: ctx.match[2] == "pay" ? true : false,
        workerId: ctx.match[1],
      },
      order: [["createdAt", "DESC"]],
      limit: 20,
    });
    
    var kassa = await Profits.sum("eurAmount", {
        where: {
          workerId: ctx.match[1],
        },
      }),
      kassaNotPay = await Profits.sum("eurAmount", {
        where: {
          status: false,
          workerId: ctx.match[1],
        },
      }),
      kassaPay = await Profits.sum("eurAmount", {
        where: {
          status: true,
          workerId: ctx.match[1],
        },
      });

    var profitsCount = await Profits.count({
        where: {
          workerId: ctx.match[1],
        },
      }),
      notPay = await Profits.count({
        where: {
          status: false,
          workerId: ctx.match[1],
        },
      }),
      pay = await Profits.count({
        where: {
          status: true,
          workerId: ctx.match[1],
        },
      });

      const count = await Profits.count({
        where: {
          status: ctx.match[2] == "pay" ? true : false,
          workerId: ctx.match[1],
        },
      });

    var buttons = chunk(
      profits.map((v, i) =>
        Markup.callbackButton(
          `${ctx.match[2] == "pay" ? "💰" : "🕓"} ${
            i + 1
          }. € ${v.eurAmount.toFixed(2)} | #${v.workerTag}`,
          `admin_profit_${v.id}`
        )
      )
    );

    if (count == 0)
      return ctx
        .answerCbQuery("🤖 На следующей странице ничего нет", true)
        .catch((err) => err);

    return ctx
      .editMessageText(
        `<b>🗂️ Текущий раздел:</b>
╰ ${ctx.match[2] == "pay" ? "💰" : "🕓"} Панель администратора -> Профиты -> ${
          ctx.match[2] == "pay"
            ? "Выплаченные профиты"
            : "Не выплаченные профиты"
        }

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

╭ 🏦 <b>Касса:</b> <b>${profitsCount}</b> профитов на сумму <b>€ ${
          kassa == null ? "0.00" : kassa.toFixed(2)
        }</b>
├ 💰 <b>Выплачено:</b> <b>${pay}</b> профитов на сумму <b>€ ${
          kassaPay == null ? "0.00" : kassaPay.toFixed(2)
        }</b>
╰ 🕓 <b>Не выплачено:</b> <b>${notPay}</b> профитов на сумму <b>€ ${
          kassaNotPay == null ? "0.00" : kassaNotPay.toFixed(2)
        }</b>`,
        {
          parse_mode: "HTML",
          disable_web_page_preview: true,
          reply_markup: Markup.inlineKeyboard([
            ...buttons,
            [
              Markup.callbackButton(
                "< Назад",
                `admin_profitsUser_${worker.id}`
              ),
            ],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};