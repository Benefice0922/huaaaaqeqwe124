const axios = require("axios")
const cheerio = require("cheerio");

module.exports = async function parser(service, link) {
    try {
        const currencies = {
            "zł": "PLN"
        }
        
        var url;
        try {
            url = new URL(link);
        } catch (err) {
            return false
        }

        if (service == "olx_pl") {
            const ad = await axios.get(encodeURI(url.href)),
                $ = cheerio.load(ad.data);

            const info = {
                title: $('[data-cy="ad_title"]').text().trim(),
                price: $('[data-testid="ad-price-container"] h3').text().trim(),
                adLink: url.href,
                serviceCode: service,
                currency: currencies["zł"]
            };
            try {
                info.photo = $(".swiper-zoom-container img").first().attr("src");
            } catch (err) { }
            return await info;
        }

    } catch (err) {
        console.log(err)
    }
}