const axios = require("axios");
const { services, Profits, users } = require("../../../database/index");

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
    await ctx.deleteMessage().catch((err) => err);

    const profitsSum = parseInt(
        await Profits.sum("rubAmount")
    );

    const Writers = await users.findAll({
        where: {
            vbiver: 1
        }
    })

    var writers = ``;

    Writers.map((v) => {
        writers += `\n▫️ 👔 <a href="https://t.me/${v.username}">${v.username}</a>`;
    });

    if (writers.length < 2 ) writers += `\n💤💤💤`;

    return ctx.replyWithPhoto({ url: "https://i.imgur.com/Fu7ECMZ.jpeg" }, { caption: `🏦 <b>Касса: €</b> ${await converter(profitsSum, "EUR")}
🎾 <b>Статус работы:</b> ${ctx.state.settings.work == true ? "WORK" : "STOP WORK"}

💳 <b>На вбиве:</b>${writers}

⚙️ <b>Отчёт работоспособности:
╰ 🌐 Домен:</b> Обычный Домен

╭ ${ctx.state.settings.sms == true ? "🎾" : "⭕️"} <b>Состояние SMS:</b> ${ctx.state.settings.sms == true ? "работает" : "не работает"}
├ ${ctx.state.settings.mail == true ? "🎾" : "⭕️"} <b>Состояние Mail:</b> ${ctx.state.settings.mail == true ? "работает" : "не работает"}
├ ${ctx.state.settings.sertSsl == true ? "🎾" : "⭕️"} <b>Состояние сертификата:</b> ${ctx.state.settings.sertSsl == true ? "работает" : "не работает"}
╰ ${ctx.state.settings.domain == true ? "🎾" : "⭕️"} <b>Состояние домена:</b> ${ctx.state.settings.domain == true ? "работает" : "не работает"}

💡 Если бот демонстрирует неверную информацию, пожалуйста, перейдите в главное меню <a href="https://t.me/uglyjs_rent_bot">бота</a> и нажмите на "Сообщить о проблеме"`, parse_mode: "HTML"})
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
