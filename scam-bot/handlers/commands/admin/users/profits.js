const { Markup } = require("telegraf");

const { Profits, users } = require("../../../../database/index");

module.exports = async (ctx) => {
  try {
    const worker = await users.findOne({
      where: {
        id: ctx.match[1],
      },
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

    return ctx
      .editMessageText(
        `<b>🗂️ Текущий раздел:</b>
╰ 📦 Панель администратора -> Объявления

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

╭ 🏦 <b>Всего профитов:</b> <b>${profitsCount}</b> профитов на сумму <b>€ ${
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
            [
              Markup.callbackButton(
                "🕓 Не выплаченные профиты",
                `admin_profits_user_${ctx.match[1]}_notpay`
              ),
              Markup.callbackButton(
                "💰 Выплаченные профиты",
                `admin_profits_user_${ctx.match[1]}_pay`
              ),
            ],
            [Markup.callbackButton("< Назад", `admin_user_${worker.username}`)],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};