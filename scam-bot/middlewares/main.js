const db = require("../database/index");
const Users = db.users;
const Settings = db.settings;

const { Markup } = require("telegraf");

module.exports = async (ctx, next) => {
  try {
    const settings = await Settings.findOne({
      where: {
        id: 1,
      },
    }).catch((err) => err);

    var user = await Users.findOrCreate({
      where: {
        id: ctx.from.id,
      },
      defaults: {
        id: ctx.from.id,
        username: ctx.from.username,
        percent: settings.percent,
      },
    }).catch((err) => err);

    ctx.state.user = user[0];
    ctx.state.settings = settings;
    ctx.state.req = user[1];

    if (ctx.state.user.banned == true)
      return ctx
        .replyWithHTML("❌ Вы были заблокированы в нашей тиме https://t.me/end_soft.")
        .catch((err) => err);
    else if (ctx.state.user.status == 2)
      return ctx
        .replyWithHTML("❌ Ваша заявка была отклонена")
        .catch((err) => err);
    else if (ctx.state.user.admin == true) return next().catch((err) => err);

    return next().catch((err) => err);
  } catch (err) {
    console.log(err);
  }
};