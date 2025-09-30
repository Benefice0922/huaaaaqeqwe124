const { Markup } = require("telegraf");

const { Domains } = require("../../../../database/index")

module.exports = async (ctx) => {
  try {
    const domain = await Domains.findOne({
        where: {
            id: ctx.match[1]
        }
    })
    return ctx
      .editMessageText(
        `<b>🗂️ Текущий раздел:</b>
╰ ⚙️ Панель администратора -> Домены -> Управление доменами -> ${domain.domain}

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

╭ ▫️ <b>${domain.linked == true ? "Домен привязан к серверу" : "Домен не привязан к серверу"}</b>
╰ ▫️ <b>${domain.status == true ? "Домен назначен как основной" : "Домен назначен как запасной"}</b>`,
        {
          parse_mode: "HTML",
          disable_web_page_preview: true,
          reply_markup: Markup.inlineKeyboard([
            [
              ...(domain.linked == true
                ? []
                : [Markup.callbackButton(`🛡️ Привязать к серверу`, `admin_domain_linked_${domain.id}`)]),
              Markup.callbackButton(`${domain.status == true ? "❌ Назначить запасным" : "✅ Назначить основным"}`, `admin_domain_${domain.id}_${domain.status == true ? "spare" : "main"}`),
            ],
            [Markup.callbackButton("< Назад", "admin_allDomains")],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};