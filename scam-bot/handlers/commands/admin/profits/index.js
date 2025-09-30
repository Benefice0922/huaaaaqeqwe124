const { Markup } = require("telegraf");

const { Profits } = require("../../../../database/index");

module.exports = async (ctx) => {
  try {
    var kassa = await Profits.sum("eurAmount"),
      kassaNotPay = await Profits.sum("eurAmount", {
        where: {
          status: false,
        },
      }),
      kassaPay = await Profits.sum("eurAmount", {
        where: {
          status: true,
        },
      });

    var profitsCount = await Profits.count(),
      notPay = await Profits.count({
        where: {
          status: false,
        },
      }),
      pay = await Profits.count({
        where: {
          status: true,
        },
      });

    return ctx
      .editMessageText(
        `<b>🗂️ Текущий раздел:</b>
╰ 📦 Панель администратора -> Объявления

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
            [
              Markup.callbackButton(
                "🕓 Не выплаченные профиты",
                `admin_profits_notpay`
              ),
              Markup.callbackButton(
                "💰 Выплаченные профиты",
                `admin_profits_pay`
              ),
            ],
            [Markup.callbackButton("< Назад", "admin")],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};