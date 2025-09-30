const { Markup } = require("telegraf");

module.exports = async (ctx) => {
  try {
    return ctx
      .editMessageText(
        `<b>🗂️ Текущий раздел:</b>
╰ ⚙️ Панель администратора -> Настройки проекта

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>

├ <b>Статус работы проекта:</b> ${
          ctx.state.settings.work == true ? "WORK" : "STOP WORK"
        }
    
╭ ${ctx.state.settings.sms == true ? "🎾" : "⭕️"} <b>Состояние SMS:</b> ${
          ctx.state.settings.sms == true ? "работает" : "не работает"
        }
├ ${ctx.state.settings.mail == true ? "🎾" : "⭕️"} <b>Состояние Mail:</b> ${
          ctx.state.settings.mail == true ? "работает" : "не работает"
        }
├ ${
          ctx.state.settings.sertSsl == true ? "🎾" : "⭕️"
        } <b>Состояние сертификата:</b> ${
          ctx.state.settings.sertSsl == true ? "работает" : "не работает"
        }
├ ${
          ctx.state.settings.domain == true ? "🎾" : "⭕️"
} <b>Состояние домена:</b> ${
          ctx.state.settings.domain == true ? "работает" : "не работает"
        }
╰ <b>${ctx.state.settings.lk == true ? "🎾" : "⭕️"} ЛК:</b> ${ctx.state.settings.lk == true ? "включен" : "выключен"}`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.callbackButton(
                `${
                  ctx.state.settings.work == true
                    ? "❌ STOP WORK"
                    : "✅ FULL WORK"
                }`,
                `${ctx.state.settings.work == true ? "stopWork" : "fullWork"}`
              ),
            ],
            [
              Markup.callbackButton(
                `${ctx.state.settings.sms == true ? "❌ SMS" : "✅ SMS"}`,
                `${ctx.state.settings.sms == true ? "offSms" : "workSms"}`
              ),
              Markup.callbackButton(
                `${ctx.state.settings.mail == true ? "❌ MAIL" : "✅ MAIL"}`,
                `${ctx.state.settings.mail == true ? "offMail" : "workMail"}`
              ),
            ],
            [
              Markup.callbackButton(
                `${ctx.state.settings.sertSsl == true ? "❌ SSL" : "✅ SSL"}`,
                `${ctx.state.settings.sertSsl == true ? "offSsl" : "workSsl"}`
              ),
              Markup.callbackButton(
                `${
                  ctx.state.settings.domain == true ? "❌ ДОМЕН" : "✅ ДОМЕН"
                }`,
                `${
                  ctx.state.settings.domain == true ? "offDomain" : "workDomain"
                }`
              ),
            ],
            [
              Markup.callbackButton(
                `${ctx.state.settings.lk == true ? "❌ ЛК" : "✅ ЛК"}`,
                `${ctx.state.settings.lk == true ? "offLk" : "workLk"}`
              ),
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
