const axios = require("axios");
const cheerio = require("cheerio");

async function parser(service, url) {
  if (service == "ebay1_de" || service == "ebay2_de") {
    const ad = await axios.get(encodeURI(url)),
      $ = cheerio.load(ad.data);
    const info = {
      title: $("h1#viewad-title").text().trim(),
      price: $("h2.boxedarticle--price").text().trim(),
      photo: $(`img#viewad-image`).first().attr("src"),
    };

    return info;
  } else if (service == "olx1_pl" || service == "olx2_pl") {
    const ad = await axios.get(encodeURI(url)),
      $ = cheerio.load(ad.data);
    const info = {
      title: $('[data-cy="ad_title"]').text().trim(),
      price: $('[data-testid="ad-price-container"] h3').text().trim(),
      photo: $(".swiper-zoom-container img").first().attr("src"),
    };

    return info;
  }
}

module.exports = async (service, url) => {
  return parser(service, url);
};