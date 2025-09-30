const { Markup } = require("telegraf");

const { items, services } = require("../../../../database/index")

module.exports = async (ctx) => {
  try {
    const item = await items.findOne({
        where: {
            id: ctx.match[1],
            workerId: ctx.from.id
        }
    })

    if(!item) return ctx.answerCbQuery("🤖 На следующей странице ничего нет", true).catch((err) => err);
    
    const serivce = await services.findOne({
        where: {
            code: item.serviceCode
        }
    })

    return ctx
      .editMessageText(
        `🗂️ <b>Текущий раздел:</b>
╰ 🧾 Профиль -> Ссылки -> Объявление

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

╭ ▫️ <b>Сервис:</b> ${serivce.title}
├ ▫️ <b>Название:</b> ${item.title}
╰ ▫️ <b>Стоимость:</b> ${item.currency} ${item.price}`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.urlButton("🌐 Перейти", `https://${serivce.domain}/pay/order/${item.id}`)],
            [
              Markup.callbackButton("💶 Цена", `changePrice_${item.id}`),
              Markup.callbackButton("♻️ Удалить", `destroyAd_${item.id}`),
            ],
            [
              Markup.callbackButton("📪 Mail", `mail_${item.id}`),
            ],
            [Markup.callbackButton("< Назад", "myAds")],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};