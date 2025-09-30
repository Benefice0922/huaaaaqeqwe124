const { Markup } = require("telegraf");
const WizardScene = require("telegraf/scenes/wizard");

const { items, services } = require("../../../../../database/index");

const parser = require("../../../../functions/createParser");

function genId() {
  var result = "";
  var characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
  var charactersLength = characters.length;
  for (var i = 0; i < 8; i++) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }
  return result;
}

module.exports = new WizardScene(
  "create_paypal_en",
  async (ctx) => {
    try {
      ctx.wizard.state.service = ctx.match[1];
      const service = await services.findOne({
        where: {
          code: ctx.wizard.state.service,
        },
      });

      const item = await items.create({
        id: genId(),
        workerId: ctx.from.id,
        currency: service.currency,
        serviceCode: service.code,
        status: service.status,
      });

      await ctx
        .editMessageText(
          `🗂️ <b>Текущий раздел:</b>
╰ 🅿️ Объявления -> ${service.title} ${service.status}.0

╭ ${service.title} ${service.status}.0
╰ 🏠 <a href="https://${service.domain}/pay/order/${item.id}">Ваше объявление</a>`,
          {
            parse_mode: "HTML",
            reply_markup: Markup.inlineKeyboard([
              [
                Markup.urlButton(
                  "🔗 Перейти",
                  `https://${service.domain}/pay/order/${item.id}`
                ),
              ],
              //   [
              //     Markup.callbackButton("🖊️ Цена", `changePrice_${item.id}`),
              //   ],
              [Markup.callbackButton("< В меню", `menu`)],
            ]),
          }
        )
        .catch((err) => err);

      return ctx.wizard.next();
    } catch (err) {
      console.log(err);
      return ctx.scene.leave();
    }
  }
);