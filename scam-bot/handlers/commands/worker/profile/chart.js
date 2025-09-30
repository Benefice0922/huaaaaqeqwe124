const { Markup } = require("telegraf");
var now = new Date();
const { Profits } = require("../../../../database/index");
const moment = require("moment");
const { Op, Sequelize } = require("sequelize");

module.exports = async (ctx) => {
  try {
    async function getCount(datee) {

        const countOne = await Profits.count({
            where: {
                workerId: ctx.from.id,
                createdAt: {
                  [Op.lt]: moment().subtract(1, 'days').toDate()
                  // moment().subtract(0, 'days').toDate()
                }
            }
        })

        const countTwo = await Profits.count({
          where: {
              workerId: ctx.from.id,
              createdAt: {
                [Op.gte]: moment().subtract(1, 'days').toDate()
                // moment().subtract(0, 'days').toDate()
              }
          }
      })

        console.log(countOne, countTwo)
    }

    console.log(moment().subtract(1, 'days').toDate())
    await getCount(-3)

    // return ctx
    //   .replyWithPhoto(
    //     {
    //       url: `https://quickchart.io/chart?v=2.9.4&c={ type: 'bar', data: { labels: ['${now.getMonth() + 1}/${now.getDate() - 7}/${now.getFullYear()}', '${now.getMonth() + 1}/${now.getDate() - 6}/${now.getFullYear()}', '${now.getMonth() + 1}/${now.getDate() - 5}/${now.getFullYear()}', '${now.getMonth() + 1}/${now.getDate() - 4}/${now.getFullYear()}','${now.getMonth() + 1}/${now.getDate() - 3}/${now.getFullYear()}', '${now.getMonth() + 1}/${now.getDate() - 2}/${now.getFullYear()}', '${now.getMonth() + 1}/${now.getDate() - 1}/${now.getFullYear()}', '${now.getMonth() + 1}/${now.getDate()}/${now.getFullYear()}'], datasets: [{ label: '💰 График профитов за неделю', data: [1, 3, 0, 5, 0, 0, 2, 1] }] }, options: { title: { display: true, text: 'Basic chart title' } } }`,
    //     },
    //     {
    //       caption: `<b>📊 Статистика в виде графика.</b>`,
    //       parse_mode: "HTML",
    //       reply_markup: Markup.inlineKeyboard([
    //         [Markup.callbackButton("♻️ Скрыть", "hide")],
    //       ]),
    //     }
    //   )
    //   .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};