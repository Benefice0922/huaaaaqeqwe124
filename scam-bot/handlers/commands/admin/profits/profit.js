const { Markup } = require("telegraf");

const {
  Profits,
  users,
  Mentors,
  items,
  services,
  countries,
} = require("../../../../database/index");

module.exports = async (ctx, page = 1) => {
  try {
    const profit = await Profits.findOne({
      where: {
        id: ctx.match[1],
      },
    });

    if (!profit)
      return ctx.answerCbQuery("🤖 Профит не найден", true).catch((err) => err);

    const worker = await users.findOne({
      where: {
        id: profit.workerId,
      },
    });

    const service = await services.findOne({
      where: {
        code: profit.serviceCode,
      },
    });

    const country = await countries.findOne({
      where: {
        code: service.country,
      },
    });

    let mentorPercent = 0;
    var mentorUsername = "";

    if (profit.mentorId != null) {
      const mentor = await Mentors.findOne({
        where: {
          workerId: profit.mentorId,
        },
      });

      mentorPercent = mentor.percent;
      mentorUsername = mentor.username;
    }

    return ctx
      .editMessageText(
        `<b>🗂️ Текущий раздел:</b>
╰ ${profit.status == true ? "💰" : "🕓"} Панель администратора -> Профиты -> ${
          profit.status == true
            ? "Выплаченные профиты"
            : "Не выплаченные профиты"
        } -> #${profit.id}

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

├ ${profit.status == true ? "♻️" : "🕓"} <b>Статус профита:</b> ${
          profit.status == true ? "Выплачено" : "Ожидает выплаты"
        }

╭ 💳 <b>Сумма профита:</b> € ${profit.eurAmount.toFixed(2)}
├ 💶 <b>Доля воркера:</b> € ${
          profit.mentorId == null
            ? (
                (parseInt(profit.eurAmount) / 100) *
                parseInt(worker.percent)
              ).toFixed(2)
            : (
                (parseInt(profit.eurAmount) / 100) * parseInt(worker.percent) -
                (parseInt(profit.eurAmount) / 100) * parseInt(mentorPercent)
              ).toFixed(2)
        }
╰ ${
          Array.from(country.title)[0] + Array.from(country.title)[1]
        } <b>Площадка:</b> ${service.title.replace(/[^a-zA-Z]+/g, "")} ${
          service.status
        }.0

╭ 👨🏻‍💻 <b>Воркер:</b> #${worker.tag} <b>(@${worker.username})</b>
╰ 🏦 <b>Кошелек для выплаты:</b> ${
          worker.wallet == null
            ? "Не установлен"
            : `<code>${worker.wallet.split("&")[1]}</code> (${
                worker.wallet.split("&")[0]
              })`
        }

${
  profit.mentorId != null
    ? `├ 🧠 <b>Наставник:</b> @${mentorUsername} <b>(${mentorPercent}%)</b>`
    : ""
}`,
        {
          parse_mode: "HTML",
          disable_web_page_preview: true,
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.callbackButton(
                "♻️ Выплачено",
                `admin_profit_${profit.id}_pay`
              ),
              Markup.callbackButton(
                "🕓 В ожидании",
                `admin_profit_${profit.id}_wait`
              ),
            ],
            [
              Markup.callbackButton(
                "❌ Удалить",
                `admin_profit_${profit.id}_destroy`
              ),
            ],
            [
              Markup.callbackButton(
                "< Назад",
                `admin_profits_${profit.status == true ? "pay" : "notpay"}`
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