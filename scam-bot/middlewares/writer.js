module.exports = async(ctx, next) => {
    try {
        try {
            if(ctx.state.user.admin == true || ctx.state.user.vbiver == true) return next()
            else if(ctx.state.user.vbiver == false) return 
        } catch (err) {
            if(ctx.state.user.admin == true || ctx.state.user.vbiver == true) return next()
            else if(ctx.state.user.vbiver == false) return 
        }
    } catch (err) {
        console.log(err)
    }
}