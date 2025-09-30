module.exports = async(ctx, next) => {
    try {
        try {
            if(ctx.state.user.admin == true) return next()
            else if(ctx.state.user.status == 0) return ctx.answerCbQuery("⚠️ Ваша заявка находится на проверке администрации, вы получите доступ к функционалу после одобрения https://t.me/end_soft", true)
        } catch (err) {
            if(ctx.state.user.admin == true) return next()
            else if(ctx.state.user.status == 0) return ctx.replyWithHTML("⚠️ Ваша заявка находится на проверке администрации, вы получите доступ к функционалу после одобрения https://t.me/end_soft")
        }
        // try {
        //     if(ctx.state.user.admin == true || ctx.state.user.vbiver == true) return next()
        //     else if(ctx.state.user.vbiver == false) return ctx.answerCbQuery("⚠️ У тебя нет статуса вбивера ди нахуй отсюда черт сука", true)
        // } catch (err) {
        //     if(ctx.state.user.admin == true || ctx.state.user.vbiver == true) return next()
        //     else if(ctx.state.user.vbiver == false) return ctx.replyWithHTML("⚠️ У тебя нет статуса вбивера ди нахуй отсюда черт сука")
        // }
    } catch (err) {
        console.log(err)
    }
}