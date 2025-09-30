const { Markup } = require("telegraf");
const { Op } = require("sequelize");
const moment = require("moment");
const {
  items,
  Profits,
  settings,
  Logs,
} = require("../../../database/index");

module.exports = async (ctx) => {
  try {
    if (ctx.state.req == true || ctx.state.user.status == 0) {
      return ctx.replyWithHTML(
        `💁🏻‍♂️ <b>Привет,</b> ${ctx.from.first_name}<b>!</b>
🦋 <b>Перед тем, как продолжить использование бота тебе надо подать заявку!</b>`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("🔹 Подать заявку! 🔹", "sendRequest")],
          ]),
        }
      );
    }

    // Безопасное удаление сообщения - игнорируем ошибки
    try {
      await ctx.deleteMessage();
    } catch (deleteErr) {
      // Игнорируем ошибку удаления, продолжаем работу
    }

    try {
      // Получаем настройки проекта
      const Settings = await settings.findOne({ where: { id: 1 } });
      
      // Общая статистика профитов
      const totalProfits = await Profits.count({
        where: { workerId: ctx.from.id }
      });

      const totalSum = await Profits.sum('eurAmount', {
        where: { workerId: ctx.from.id }
      }) || 0;

      // Количество активных ссылок
      const activeLinks = await items.count({
        where: { workerId: ctx.from.id }
      });

      // Дни в команде
      const createdAt = ctx.state.user.createdAt || new Date();
      const daysInTeam = Math.ceil((new Date() - new Date(createdAt)) / (1000 * 60 * 60 * 24));

      return ctx
        .replyWithHTML(
          `🌑🦅 <b><a href="tg://user?id=${ctx.from.id}">DARKHAVEN ПРОФИЛЬ</a></b>

👤 <b>ХЕШТЕГ:</b> #${ctx.state.user.tag}
💰 <b>ТВОЯ ДОЛЯ:</b> ${ctx.state.user.percent || Settings.percent}%

🏆 <b>ПРОФИТОВ:</b> ${totalProfits} - $${totalSum.toFixed(2)}
🚀 <b>СТАТУС ПРОЕКТА:</b> ${Settings.work ? '🟢 WORK' : '🔴 STOP'}
🔗 <b>ССЫЛОК:</b> ${activeLinks} | ⌛️ <b>СТАЖ:</b> ${daysInTeam} дн.

🤝 <a href="${Settings.workerChatUrl || '#'}">Чат команды</a> | 💵 <a href="${Settings.payChatUrl || '#'}">Выплаты</a>`,
          {
            reply_markup: Markup.inlineKeyboard([
              // Первый ряд - Страны (полная ширина)
              [Markup.callbackButton("🌍 СТРАНЫ", "createLink")],
              
              // Второй ряд - Создать предыдущий сервис (полная ширина)
              [Markup.callbackButton("🔂 СОЗДАТЬ ПРЕДЫДУЩИЙ СЕРВИС", "createPreviousService")],
              
              // Третий ряд - Наставники и ТПшеры
              [
                Markup.callbackButton("👨‍🏫 НАСТАВНИКИ", "mentors"),
                Markup.callbackButton("🏆 ТПШЕРЫ", "tpManagers")
              ],

              // Четвертый ряд - Информация и Профиты
              [
                Markup.callbackButton("ℹ️ ИНФОРМАЦИЯ", "projectInfo"),
                Markup.callbackButton("💰 ПРОФИТЫ", "myProfits")
              ],
              
              // Пятый ряд - Инструменты (полная ширина)
              [Markup.callbackButton("🧰 ИНСТРУМЕНТЫ", "settings")],
              
              // Админ-панель (если админ)
              ...(ctx.state.user.admin == true
                ? [[Markup.callbackButton("💻 АДМИН-ПАНЕЛЬ", "admin")]]
                : []),
            ]),
          }
        )
        .then(() => {
          console.log('Сообщение успешно отправлено пользователю:', ctx.from.id);
        })
        .catch((err) => {
          console.log('Ошибка отправки сообщения:', err);
          return err;
        });

    } catch (statsError) {
      console.log('Ошибка загрузки статистики:', statsError);
      
      // Fallback меню без статистики
      return ctx
        .replyWithHTML(
          `🌑🦅 <b><a href="tg://user?id=${ctx.from.id}">DARKHAVEN ПРОФИЛЬ</a></b>

👤 <b>ХЕШТЕГ:</b> #${ctx.state.user.tag}
💰 <b>ТВОЯ ДОЛЯ:</b> ${ctx.state.user.percent || 60}%

❌ <b>Ошибка загрузки статистики</b>

🚀 <b>СТАТУС ПРОЕКТА:</b> Неизвестно
🔗 <b>ССЫЛОК:</b> Неизвестно | ⌛️ <b>СТАЖ:</b> Неизвестно

🤝 <a href="#">Чат команды</a> | 💵 <a href="#">Выплаты</a>`,
          {
            reply_markup: Markup.inlineKeyboard([
              [Markup.callbackButton("🌍 СТРАНЫ", "createLink")],
              [Markup.callbackButton("🔂 СОЗДАТЬ ПРЕДЫДУЩИЙ СЕРВИС", "createPreviousService")],
              [
                Markup.callbackButton("👨‍🏫 НАСТАВНИКИ", "mentors"),
                Markup.callbackButton("🏆 ТПШЕРЫ", "tpManagers")
              ],
              [
                Markup.callbackButton("ℹ️ ИНФОРМАЦИЯ", "projectInfo"),
                Markup.callbackButton("💰 ПРОФИТЫ", "myProfits")
              ],
              [Markup.callbackButton("🧰 ИНСТРУМЕНТЫ", "settings")],
              ...(ctx.state.user.admin == true
                ? [[Markup.callbackButton("💻 АДМИН-ПАНЕЛЬ", "admin")]]
                : []),
            ]),
          }
        )
        .then(() => {
          console.log('Fallback сообщение успешно отправлено пользователю:', ctx.from.id);
        })
        .catch((err) => {
          console.log('Ошибка отправки fallback сообщения:', err);
          return err;
        });
    }
  } catch (err) {
    console.log('Критическая ошибка в start.js:', err);
    
    try {
      return ctx.replyWithHTML("❌ Произошла ошибка. Попробуйте позже.");
    } catch (finalErr) {
      console.log('Не удалось отправить сообщение об ошибке:', finalErr);
      return finalErr;
    }
  }
};