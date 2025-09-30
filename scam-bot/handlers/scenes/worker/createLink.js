const { Markup } = require("telegraf")
const WizardScene = require("telegraf/scenes/wizard")

const db = require("../../../database/index")
const Items = db.items
const Services = db.services

const checkUrl = require('../../functions/checkUrl')
const parser = require('../../functions/parser')

function genId() {
    var result = '';
    var characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
    var charactersLength = characters.length;
    for (var i = 0; i < 8; i++) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }
    return result;
}

module.exports = new WizardScene(
    "createLink",
    async (ctx) => {
        try {
            ctx.wizard.state.service = ctx.match[1]

            await ctx.deleteMessage().catch((err) => err)

            await ctx.replyWithHTML("🤖 <i>Отправь мне ссылку на объявление, если такой сервис есть, я определю его</i>", {
                reply_markup: Markup.inlineKeyboard([
                    [Markup.callbackButton("Отмена", "cancel")]
                ])
            }).catch((err) => err)

            return ctx.wizard.next()
        } catch (err) {
            console.log(err)
            return ctx.scene.leave()
        }
    },
    async (ctx) => {
        try {
            ctx.wizard.state.service = ctx.message.text

            const status = await checkUrl(ctx.message.text)
            await ctx.replyWithHTML("⏳ <i>Определяю сервис...</i>").catch((err) => err)

            if (status.split("&")[0] == "false") {
                await ctx.replyWithHTML(`<i>${status.split("&")[1]}</i>`).catch((err) => err)
                return ctx.scene.leave()
            } else {
                await ctx.replyWithHTML("✅ <i>Нашел сервис, начинаю парсинг...</i>").catch((err) => err)
                const info = await parser(status, ctx.message.text)

                const Item = await Items.create({
                    id: genId(),
                    workerId: ctx.from.id,
                    title: info.title,
                    photo: info.photo,
                    price: info.price,
                    serviceCode: info.serviceCode,
                    currency: info.currency
                })
                await ctx.replyWithHTML("✅ <i>Ссылка сгенерирована!</i>", {
                    reply_markup: Markup.inlineKeyboard([
                        [Markup.urlButton("Перейти", `https://google.com/get/${Item.id}`)]
                    ])
                })
            }

            return ctx.scene.leave()
        } catch (err) {
            console.log(err)
            return ctx.scene.leave()
        }
    },
)