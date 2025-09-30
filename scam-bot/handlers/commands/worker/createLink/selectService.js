const { Markup } = require('telegraf')
const chunk = require("chunk")

const db = require("../../../../database/index")
const Services = db.services

module.exports = async (ctx) => {
    try {
        const services = await Services.findAll({
            where: {
                work: true,
                country: ctx.match[1]
            }
        })

        var buttons = chunk(
            services.map((v) =>
                Markup.callbackButton(`${v.title} ${v.status}.0`, `service_${v.code}`)
            )
        )

        if (buttons.length < 1) {
            buttons = [[Markup.callbackButton("Сервисов нет :(", "none")]];
        }

        return ctx.editMessageText(`🗂️ <b>Текущий раздел:</b>
╰ 👨🏼‍🏫 Страны -> Сервисы

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>`, {
    parse_mode: "HTML",
    reply_markup: Markup.inlineKeyboard([
        ...buttons,
        [Markup.callbackButton("< Назад", "createLink")]
    ])
}).catch((err) => err);
    } catch (err) {
        console.log(err)
    }
}