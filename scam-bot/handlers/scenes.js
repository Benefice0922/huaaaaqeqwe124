const Stage = require("telegraf/stage");
const { Markup } = require("telegraf");

const sendRequest = require("./scenes/worker/sendRequest");

const createLink = require("./scenes/worker/createLink");

const addProfit = require("./scenes/admin/addProfit");
const sendMentorReq = require("./scenes/worker/sendMentorReq");

const report = require("./scenes/worker/report");

const customErr = require("./scenes/vbiv/custom");

const changePrice = require("./scenes/worker/changePrice");
const changeWallet = require("./scenes/worker/changeWallet");

const changeTag = require("./scenes/worker/changeTag")

const replySupport = require("./scenes/worker/replySupport")

const adminAlert = require("./scenes/admin/adminAlert")
const changeDomain = require("./scenes/admin/changeDomain")

const addAccount = require("./scenes/admin/domains/addAccount")
const addDomain = require("./scenes/admin/domains/addDomain")
const addCf = require("./scenes/admin/domains/addCf")
const linkDomain = require("./scenes/admin/domains/linkDomain")

const mentorChangePercent = require("./scenes/admin/mentors/changePercent")
const mentorChangeAbout = require("./scenes/admin/mentors/changeAbout")
const globalMentorPercent = require("./scenes/admin/mentors/globalPercent")

const adminChangePrice = require("./scenes/admin/ads/changePrice")

const setSmartsupp = require("./scenes/worker/setSmartsupp")

const ebay1De = require("./scenes/worker/createLink/de/ebay1");
const ebay2De = require("./scenes/worker/createLink/de/ebay2");
const dhl1De = require("./scenes/worker/createLink/de/dhl1");
const dhl2De = require("./scenes/worker/createLink/de/dhl2");
const vinted1De = require("./scenes/worker/createLink/de/vinted1");
const vinted2De = require("./scenes/worker/createLink/de/vinted2");
const kolesa1Kz = require("./scenes/worker/createLink/kz/kolesa1");

const willhaben1Au = require("./scenes/worker/createLink/au/willhaben1");
const willhaben2Au = require("./scenes/worker/createLink/au/willhaben2");
const vinted2Au = require("./scenes/worker/createLink/au/vinted2");

const paypalEn = require("./scenes/worker/createLink/en/paypal");

const olx2Pl = require("./scenes/worker/createLink/pl/olx");
const changeWorkerPercent = require("./scenes/admin/changeWorkerPercent");

const dba2Dk = require("./scenes/worker/createLink/dk/dba2");

const adMailer = require("./scenes/worker/adMailer");

const stage = new Stage([
  adMailer,
  
  dba2Dk,
  
  olx2Pl,

  paypalEn,
  kolesa1Kz,
  willhaben1Au,
  willhaben2Au,
  vinted2Au,

  ebay1De, 
  ebay2De,
  dhl1De,
  dhl2De,
  vinted1De,
  vinted2De,

  changeWorkerPercent,

  setSmartsupp,
  
  adminChangePrice,
  
  mentorChangePercent,
  mentorChangeAbout,
  globalMentorPercent,
  
  addDomain,
  addAccount,
  addCf,
  linkDomain,

  changeDomain,
  adminAlert,
  
  replySupport,
  
  changeTag,
  changeWallet,
  
  changePrice,
  
  customErr,
  
  sendRequest, 
  
  createLink, 
  
  addProfit,

  sendMentorReq,
  report,
]);

stage.action("requestCancel", async (ctx) => {
  try {
    await ctx
      .editMessageText("<b>⚡️ Чтобы начать заново нажмите кнопку ниже</b>", {
        parse_mode: "HTML",
        reply_markup: Markup.inlineKeyboard([
          [Markup.callbackButton("⚡️", "sendRequest")],
        ]),
      })
      .catch((err) => err);
    return ctx.scene.leave();
  } catch (err) {
    console.log(err);
    return ctx.reply("Произошла неизвестная ошибка").catch((err) => err);
  }
});

stage.action("cancel", async (ctx) => {
  try {
    await ctx
      .editMessageText("<b>🧑‍💻 Вернитесь в меню.</b>", {
        parse_mode: "HTML",
        reply_markup: Markup.inlineKeyboard([
          [Markup.callbackButton("< Назад", "menu")],
        ]),
      })
      .catch((err) => err);
    return ctx.scene.leave();
  } catch (err) {
    console.log(err);
    return ctx.reply("Произошла неизвестная ошибка").catch((err) => err);
  }
});

module.exports = stage;