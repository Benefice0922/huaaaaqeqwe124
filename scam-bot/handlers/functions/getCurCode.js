module.exports = async function getCode(currency) {
  const codes = {
    PLN: "zł",
    EUR: "€",
    DKK: "kr",
  };

  return codes[currency];
};