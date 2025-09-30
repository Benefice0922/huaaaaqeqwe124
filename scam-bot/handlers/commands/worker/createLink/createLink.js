const { Markup } = require('telegraf')
const chunk = require("chunk")

const db = require("../../../../database/index")
const Countries = db.countries
const settings = db.settings

module.exports = async (ctx) => {
    try {
        if(ctx.state.settings.work == false) {
            return ctx
            .answerCbQuery(
              `❌ В проекте назначен STOP WORK`
            )
        }

        // Получаем настройки для ссылок на чаты
        const Settings = await settings.findOne({ where: { id: 1 } });

        const countries = await Countries.findAll({
            where: {
                work: true
            }
        })

        var buttons = chunk(
            countries.map((v) =>
                Markup.callbackButton(v.title, `country_${v.code}`)
            )
        )

        if (buttons.length < 1) {
            buttons = [[Markup.callbackButton("Стран нет :(", "none")]];
        }

        return ctx.editMessageText(`🌑🦅 <b>DARKHAVEN » 🌍 Страны</b>

╭ ▫️ <b>Username:</b> ${ctx.from.first_name}
├ ▫️ <b>User ID:</b> ${ctx.from.id}
╰ ▫️ <b>Tag:</b> #${ctx.state.user.tag}

🤝 <a href="${Settings.workerChatUrl || 'https://t.me/+hwl_TUJA0P5kNTRk'}">Чат команды</a> | 💵 <a href="${Settings.payChatUrl || 'https://t.me/+mqamVM1dc2c2MWY8'}">Выплаты</a>`, {
            parse_mode: "HTML",
            reply_markup: Markup.inlineKeyboard([
                // Первый ряд - Мои ссылки
                [Markup.callbackButton("🔗 МОИ ССЫЛКИ", "myAds")],
                [Markup.callbackButton("🔂 СОЗДАТЬ ПРЕДЫДУЩИЙ СЕРВИС", "createPreviousService")],
                // Страны
                ...buttons,
                // Назад
                [Markup.callbackButton("🔙 НАЗАД", "menu")]
            ])
        }).catch((err) => err);
    } catch (err) {
        console.log(err)
    }
}