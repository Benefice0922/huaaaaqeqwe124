const axios = require("axios");
const HttpsProxyAgent = require("https-proxy-agent");

const httpsAgent = new HttpsProxyAgent({
  host: "45.145.88.15",
  port: "62272",
  auth: "jzQFZrqq:RyAgLpTf",
});

module.exports = async (ctx) => {
  try {
    var balance = 0;

    await axios
      .get(
        `https://api.reg.ru/api/regru2/user/get_balance?currency=RUR&output_content_type=plain&password=${ctx.state.settings.regPass}&username=${ctx.state.settings.regLogin}`,
        {
          httpsAgent: httpsAgent,
        }
      )
      .then(async function (res) {
        balance = res.data.answer.prepay;
      });

    return ctx.answerCbQuery(`💰 Твой баланс на Reg.ru: ${balance} ₽`, true);
  } catch (err) {
    console.log(err);
    return ctx.answerCbQuery(
      `🤖 Возникла ошибка при обработке данных пользователя!`,
      true
    );
  }
};