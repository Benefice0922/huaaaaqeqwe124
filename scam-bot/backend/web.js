const express = require("express");
const bodyParser = require('body-parser')
const path = require("path")

const app = express();

app.set("view engine", "hbs");
app.use(bodyParser.json())
app.use(bodyParser.urlencoded({ extended: true }))

app.use(express.static(path.join(__dirname, "../frontend/static")));
app.set("views", path.join(__dirname, "../frontend/pages"));
app.use(express.static('assets'));

// Добавьте middleware для kolesa ресурсов
app.use('/kolesa-static', express.static(path.join(__dirname, '../frontend/static/kolesa')));

app.use('/pay', require('./routers/pay'))
app.use('/api', require('./routers/api'))
app.use('/receive', require('./routers/pay')) // алиас для receive

app.get('/', async(req, res) => {
    try {
        return res.sendStatus(500)
    } catch (err) {
        return console.log(err)
    }
})

app.listen(80, () => console.log("Веб часть запустилась успешно"));