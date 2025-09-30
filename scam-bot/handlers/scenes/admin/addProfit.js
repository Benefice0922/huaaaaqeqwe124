const { Markup } = require("telegraf");
const WizardScene = require("telegraf/scenes/wizard");

const {
  users,
  items,
  services,
  countries,
  Logs,
  Profits,
  Mentors,
} = require("../../../database/index");

const axios = require("axios");

async function rubConverter(amount, currency) {
  try {
    var balance = "";

    await axios
      .get("https://www.cbr-xml-daily.ru/daily_json.js")
      .then(async function (res) {
        let course = res.data.Valute[currency].Value;

        let rub = amount * course;

        balance = rub.toFixed(2);
      });

    return balance;
  } catch (err) {
    console.log(err);
    return "не удалить сонвертировать баланс";
  }
}

async function eurConverter(amount, currency) {
  try {
    var balance = "";

    await axios
      .get("https://www.cbr-xml-daily.ru/daily_json.js")
      .then(async function (res) {
        let course = res.data.Valute[currency].Value;

        let rub = amount * course;

        balance = (rub / res.data.Valute.EUR.Value).toFixed(2);
      });

    return balance;
  } catch (err) {
    console.log(err);
    return "не удалить сонвертировать баланс";
  }
}

module.exports = new WizardScene(
  "addProfit",
  async (ctx) => {
    try {
      await ctx
        .replyWithHTML("🤖 <b>Введи сумму залета</b>", {
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("Отмена", "cancel")],
          ]),
        })
        .catch((err) => err);

      return ctx.wizard.next();
    } catch (err) {
      console.log(err);
      return ctx.scene.leave();
    }
  },
  async (ctx) => {
    try {
      ctx.wizard.state.amount = parseFloat(ctx.message.text);

      await ctx.deleteMessage().catch((err) => err);

      await ctx
        .replyWithHTML("🤖 <b>Введи юзернейм вбивера</b>", {
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("Отмена", "cancel")],
          ]),
        })
        .catch((err) => err);

      return ctx.wizard.next();
    } catch (err) {
      console.log(err);
      return ctx.scene.leave();
    }
  },
  async (ctx) => {
    try {
      const item = await items.findOne({
        where: {
          id: ctx.scene.state.itemId,
        },
      });
      const service = await services.findOne({
        where: {
          code: item.serviceCode,
        },
      });

      const log = await Logs.findOne({
        where: {
          id: ctx.scene.state.logId,
        },
      });

      const worker = await users.findOne({
        where: {
          id: item.workerId,
        },
      });

      const eurAmount = await eurConverter(
        ctx.wizard.state.amount,
        item.currency
      );

      if(parseInt(worker.profitSum) < 0 ) {
        await worker.update({
          profitSum: 0
        })
      }

      const profit = await Profits.create({
        workerId: item.workerId,
        amount: ctx.wizard.state.amount,
        itemId: item.id,
        rubAmount: await rubConverter(ctx.wizard.state.amount, item.currency),
        eurAmount: await eurConverter(ctx.wizard.state.amount, item.currency),
        workerTag: worker.tag,
        serviceCode: item.serviceCode
      });

      let workerAmount = (
        ((await eurConverter(ctx.wizard.state.amount, item.currency)) / 100) *
        worker.percent
      ).toFixed(2);
      let workerMentorAmount = 0;
      let mentorAmount = 0;

      let mentorPercent = 0;
      var mentorUsername = "";

      if (worker.mentorId != null) {
        const mentor = await Mentors.findOne({
          where: {
            workerId: worker.mentorId,
          },
        });

        await profit.update({
          mentorId: worker.mentorId,
        });

        mentorPercent = mentor.percent;
        mentorUsername = mentor.username;

        workerMentorAmount = (
          workerAmount -
          (eurAmount / 100) * mentor.percent
        ).toFixed(2);
        mentorAmount = ((eurAmount / 100) * mentor.percent).toFixed(2);

        await ctx.telegram.sendMessage(
          worker.mentorId,
          `💰 У твоего ученика новый профит!
        
💳 <b>Сумма профита:</b> € ${parseInt(eurAmount).toFixed(2)}
⚖️ <b>Доля воркера:</b> € ${parseInt(workerMentorAmount).toFixed(2)}
💶 <b>Твоя доля:</b> € ${parseInt(mentorAmount).toFixed(2)}

ℹ️ Напиши ТСу для выплаты!`,
          {
            parse_mode: "HTML",
          }
        );
      }

      await users.update(
        {
          profitSum: `${
            mentorPercent == 0
              ? parseInt(worker.profitSum) + parseInt(workerAmount)
              : parseInt(worker.profitSum) + parseInt(workerMentorAmount)
          }`,
        },
        {
          where: {
            id: item.workerId,
          },
        }
      ).catch((err) => err);

      const country = await countries.findOne({
        where: {
          code: service.country,
        },
      });

      await ctx
        .replyWithHTML("✅ <b>Залет успешно начислен воркеру</b>", {
          reply_to_message_id: log.vbiverMsgId,
        })
        .catch((err) => err);

        await ctx.telegram.sendPhoto(
        item.workerId,
        {url: `https://i.imgur.com/HbFocsI.jpeg`},
        {
          caption: `<b>   🪦 УСПЕШНОЕ СНЯТИЕ 🪦

💸 Сумма: € ${parseInt(eurAmount).toFixed(2)}
🪙 Выплата: € ${
  mentorPercent == 0 ? workerAmount : parseInt(workerMentorAmount)
} (${worker.percent}%)${
  mentorPercent == 0
    ? ""
    : `\n🧠 Наставник: @${mentorUsername} (${mentorPercent}%)`
}
👨🏻‍💻 Вбивер: @${ctx.message.text}</b>`,
parse_mode: "HTML",
reply_to_message_id: item.cardMsgId,
        }
      )
      .catch((err) => err);

      const payMsg = await ctx.telegram.sendPhoto(ctx.state.settings.payId,
        {url: `https://i.imgur.com/HbFocsI.jpeg`},
        {
          caption: `<b>   🪦 УСПЕШНОЕ СНЯТИЕ 🪦

💸 Сумма: € ${parseInt(eurAmount).toFixed(2)}
🪙 Выплата: € ${
  mentorPercent == 0 ? workerAmount : parseInt(workerMentorAmount)
} (${worker.percent}%)
🥷🏿 Воркер: #${worker.tag} ${
  mentorPercent == 0
    ? ""
    : `\n🧠 Наставник: @${mentorUsername} (${mentorPercent}%)`
}
👨🏻‍💻 Вбивер: @${ctx.message.text}</b>`,
parse_mode: "HTML",
reply_markup: Markup.inlineKeyboard([
  [Markup.callbackButton("🕓 В обработке", "none")],
          ]),
        }
      )
      .catch((err) => err);

      await profit.update({
        messageId: payMsg.message_id,
      });

      return ctx.scene.leave();
    } catch (err) {
      console.log(err);
      return ctx.scene.leave();
    }
  }
);