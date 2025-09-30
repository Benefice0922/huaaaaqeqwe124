const { Markup } = require("telegraf");

module.exports = async (ctx) => {
  try {
    const user = ctx.state.user;
    
    return ctx
      .editMessageText(
        `🌑🦅 <b>DARKHAVEN » 🧰 ИНСТРУМЕНТЫ</b>

╭ ▫️ <b>Username:</b> ${ctx.from.first_name}
├ ▫️ <b>User ID:</b> ${ctx.from.id}
╰ ▫️ <b>Tag:</b> #${ctx.state.user.tag}

├ ▫️ <b>Тип ТП:</b> ${user.supportType === "bot" ? "Через бота" : "Smartsupp"}
├ ▫️ <b>Кошелек:</b> ${user.wallet || "Не указан"}
├ ▫️ <b>Шаблон профиля:</b> ${user.profileTemplate || "По умолчанию"}
├ ▫️ <b>Рассылка в боте:</b> ${user.botNotifications ? "ВКЛ" : "ВЫКЛ"}
├ ▫️ <b>Тип страницы:</b> ${user.pageType === "card" ? "КАРТА" : "ЛК"}
╰ ▫️ <b>Сервис в профитах:</b> ${user.profitService || "Не указан"}`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            // Первый ряд
            [
              Markup.callbackButton("TAG", "changeTag"),
              Markup.callbackButton("КОШЕЛЕК", "wallet")
            ],
            // Второй ряд  
            [
              Markup.callbackButton("ШАБЛОНЫ ТП", "tpTemplates"),
              Markup.callbackButton("АВТО ТП", "autoTp")
            ],
            // Третий ряд
            [Markup.callbackButton("НАСТРОЙКИ ТП", "tpSettings")],
            // Четвертый ряд
            [Markup.callbackButton("НАСТРОЙКА ПРОФИЛЯ", "profileSettings")],
            // Пятый ряд
            [Markup.callbackButton("РАССЫЛКА В БОТЕ: ВКЛ/ВЫКЛ", "toggleBotNotifications")],
            // Шестой ряд
            [Markup.callbackButton("СКРЫТЬ СЕРВИС: ВКЛ/ВЫКЛ", "toggleServiceVisibility")],
            // Седьмой ряд - переключатель типа страницы
            [Markup.callbackButton(`ПЕРЕКЛЮЧИТЬ: ${user.pageType === "card" ? "ЛК → КАРТА" : "КАРТА → ЛК"}`, "togglePageType")],
            // Восьмой ряд - системные функции
            [
              Markup.callbackButton("БОТ", "botSettings"),
              Markup.callbackButton("SMARTSUPP", "smartsuppSettings")
            ],
            // Девятый ряд
            [Markup.callbackButton("ТПШЕР КОМАНДЫ", "tpManagerSettings")],
            // Десятый ряд
            [
              Markup.callbackButton("СМЕНА ИМЕНИ", "changeName"),
              Markup.callbackButton("СМЕНА ФОТО", "changePhoto")
            ],
            // Одиннадцатый ряд
            [Markup.callbackButton("ВЫБОР ТП", "selectTp")],
            // Оставляем как было
            [Markup.callbackButton("🌐 ДОСТУП К САЙТУ", "siteStatus")],
            [Markup.callbackButton("⚠️ ЖАЛОБЫ И ПРЕДЛОЖЕНИЯ", "report")],
            // Назад
            [Markup.callbackButton("🔙 НАЗАД", "menu")]
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};