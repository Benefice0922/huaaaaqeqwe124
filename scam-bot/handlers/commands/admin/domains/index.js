const { Markup } = require("telegraf");
const { Domains } = require("../../../../database/index");

module.exports = async (ctx) => {
  try {
    const count = await Domains.count();

    const domain = await Domains.findOne({
      where: {
        status: true,
        linked: true,
      },
    });

    return ctx
      .editMessageText(
        `<b>🗂️ Текущий раздел:</b>
╰ 🌐 Панель администратора -> Домены

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

╭ ▫️ <b>Текущий домен:</b> ${domain == null ? "не выбран" : domain.domain}
╰ ▫️ <b>Кол-во подключенных доменов:</b> ${count} шт.`,
        {
          parse_mode: "HTML",
          disable_web_page_preview: true,
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.callbackButton("🛡️ Аккаунт Cloudflare.ru", "admin_cf"),
              Markup.callbackButton("🌐 Аккаунт Reg.ru", "admin_regru"),
            ],
            [
                Markup.callbackButton("⚙️ Домены", "admin_allDomains"),
                Markup.callbackButton("💸 Купить домен", "admin_addDomain"),
            ],
            [
              Markup.callbackButton("📎 Добавить домен", "admin_linkDomain"),
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