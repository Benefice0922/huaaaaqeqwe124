const { Markup } = require("telegraf");
const { Domains } = require("../../../../database/index");

module.exports = async (ctx) => {
  try {
    const domain = await Domains.findOne({
      where: {
        status: true,
        linked: true,
      },
    });

    const { count, rows } = await Domains.findAndCountAll();

    var buttons = rows.map((v, i) => [
      Markup.callbackButton(
        `${i + 1}. ${v.status == true ? "✅" : "❌"} ${v.domain}`, `admin_domain_${v.id}`
      ),
    ]);

    if(count == 0) return ctx.answerCbQuery("🤖 На следующей странице ничего нет", true).catch((err) => err);

    return ctx
      .editMessageText(
        `<b>🗂️ Текущий раздел:</b>
╰ ⚙️ Панель администратора -> Домены -> Управление доменами

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

╭ ▫️ <b>Текущий домен:</b> ${domain == null ? "не выбран" : domain.domain}
╰ ▫️ <b>Кол-во подключенных доменов:</b> ${count} шт.`,
        {
          parse_mode: "HTML",
          disable_web_page_preview: true,
          reply_markup: Markup.inlineKeyboard([
            ...buttons,
            [Markup.callbackButton("< Назад", "admin_domains")],
          ]),
        }
      )
      // .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};