module.exports = async(ctx, next) => {
    try {
        try {
            if(ctx.state.user.admin == true) return next().catch((err) => err);
            else if(ctx.state.user.status == 0) return ctx.answerCbQuery("⚠️ Ваша заявка находится на проверке администрации, вы получите доступ к функционалу после одобрения", true)
        } catch (err) {
            if(ctx.state.user.admin == true) return next().catch((err) => err);
            else if(ctx.state.user.status == 0) return ctx.replyWithHTML("⚠️ Ваша заявка находится на проверке администрации, вы получите доступ к функционалу после одобрения")
        }
        
        return next()
    } catch (err) {
        console.log(err)
    }
}