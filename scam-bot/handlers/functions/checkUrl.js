const allDomains = ["www.olx.pl", "m.olx.pl", "olx.pl"];

module.exports = async function parser(link) {
    try {
        var url

        try {
            url = new URL(link);
        } catch (err) {
            return `${false}&❌ Введи валидную ссылку`
        }

        if (!allDomains.includes(url.host)) {
            return `${false}&❌ Данного сервиса в боте не существует`

        }
        const serivces = {
            "www.olx.pl": "olx_pl"
        }

        return serivces[url.host];
    } catch (err) {
        console.log(err)
    }
}