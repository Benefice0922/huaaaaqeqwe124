const { Composer, Markup } = require("telegraf");
const bot = new Composer(async (ctx, next) => next());

const {
  users,
  Domains,
  services,
  Profits,
  Mentors,
  items,
} = require("./database/index");

bot.use(require("./middlewares/admin"));

bot.command("admin", require("./handlers/commands/admin/panel"));
bot.action("admin", require("./handlers/commands/admin/panel"));

bot.action(/^admin_changePercent_(\d+)$/, async (ctx) => {
  return ctx.scene.enter("changeWorkerPercent");
});

bot.action("admin_profits", require("./handlers/commands/admin/profits/index"));
bot.action(
  /^admin_profits_(notpay|pay)$/,
  require("./handlers/commands/admin/profits/list")
);
bot.action(
  /^admin_profit_(\d+)$/,
  require("./handlers/commands/admin/profits/profit")
);
bot.action(/^admin_profit_(\d+)_(pay|wait|destroy)$/, async (ctx) => {
  try {
    const profit = await Profits.findOne({
      where: {
        id: ctx.match[1],
      },
    });

    if (!profit)
      return ctx.answerCbQuery(`🤖 Профит не найден`, true).catch((err) => err);

    const worker = await users.findOne({
      where: {
        id: profit.workerId,
      },
    });

    let mentorPercent = 0;

    if (profit.mentorId != null) {
      const mentor = await Mentors.findOne({
        where: {
          workerId: profit.mentorId,
        },
      });

      mentorPercent = mentor.percent;
    }

    if (ctx.match[2] == "destroy") {
      await users.update(
        {
          profitSum:
            worker.profitSum -
            parseInt(
              mentorPercent == 0
                ? (parseInt(profit.amount) / 100) * parseInt(worker.percent)
                : (parseInt(profit.amount) / 100) * parseInt(worker.percent) -
                    (parseInt(profit.amount) / 100) * parseInt(mentorPercent)
            ),
        },
        {
          where: {
            id: profit.workerId,
          },
        }
      );
      await ctx.telegram
        .deleteMessage(ctx.state.settings.payId, profit.messageId)
        .catch((err) => err);

      await profit.destroy();

      await ctx
        .answerCbQuery(`✅ Профит был успешно удален`, true)
        .catch((err) => err);

      await ctx.telegram.sendMessage(
        profit.workerId,
        `❌ Твой профит на сумму <b>€ ${profit.eurAmount}</b> был удален администратором <b>@${ctx.from.username}</b>`,
        {
          parse_mode: "HTML",
        }
      );

      return require("./handlers/commands/admin/profits/index")(ctx);
    }

    await profit.update({
      status: ctx.match[2] == "pay" ? true : false,
    });

    await ctx
      .answerCbQuery(`✅ Статус профита был https://t.me/end_soft изменен`, true)
      .catch((err) => err);

    await ctx.telegram
      .editMessageReplyMarkup(
        ctx.state.settings.payId,
        profit.messageId,
        profit.messageId,
        Markup.inlineKeyboard([
          [
            Markup.callbackButton(
              `${ctx.match[2] == "pay" ? "♻️ Выплачено" : "🕓 В обработке"}`,
              "none"
            ),
          ],
        ])
      )
      .catch((err) => err);

    await ctx.telegram.sendMessage(
      profit.workerId,
      `${ctx.match[2] == "pay" ? "♻️" : "🕓"} Твой профит на сумму <b>€ ${
        profit.eurAmount
      }</b> был переведен в статус <b>${
        ctx.match[2] == "pay" ? "выплачено" : "ожидания"
      }</b>`,
      {
        parse_mode: "HTML",
      }
    );

    return require("./handlers/commands/admin/profits/profit")(ctx);
  } catch (err) {
    console.log(err);
    try {
      return ctx.answerCbQuery(
        "🤖 Возникла ошибка при обработке https://t.me/end_soft данных пользователя!",
        true
      );
    } catch (err) {
      return ctx.replyWithHTML(
        "🤖 Возникла ошибка при обработке данных пользователя!"
      );
    }
  }
});

bot.action("admin_items", require("./handlers/commands/admin/ads/index"));
bot.action("admin_items_destroyAll", async (ctx) => {
  try {
    const destroy = await items.destroy({
      where: {},
      truncate: true,
    });

    await ctx
      .answerCbQuery(
        `♻️ Удалено: ${destroy}!
  
❣️ Спасибо, что очищаете БД!`,
        true
      )
      .catch((err) => err);

    return require("./handlers/commands/admin/ads/index")(ctx);
  } catch (err) {
    console.log(err);
    try {
      return ctx.answerCbQuery(
        "🤖 Возникла ошибка при обработке данных пользователя!",
        true
      );
    } catch (err) {
      return ctx.replyWithHTML(
        "🤖 Возникла ошибка при обработке данных пользователя!"
      );
    }
  }
});
bot.action("admin_items_list", require("./handlers/commands/admin/ads/list"));
bot.hears(
  /^\/item ?([A-Za-z0-9_]+)$/,
  require("./handlers/commands/admin/ads/item2.js")
);
bot.action(/^admin_item_(.+)$/, require("./handlers/commands/admin/ads/item"));
bot.action(/^admin_changePrice_(.+)$/, async (ctx) => {
  const item = await items.findOne({
    where: {
      id: ctx.match[1],
    },
  });

  if (!item)
    return ctx
      .answerCbQuery(`♻️ Объявление с ID ${ctx.match[1]} не найдено!`, true)
      .catch((err) => err);

  return ctx.scene.enter("adminChangePrice");
});
bot.action(/^admin_destroyAd_(.+)$/, async (ctx) => {
  try {
    const item = await items.findOne({
      where: {
        id: ctx.match[1],
      },
    });

    if (!item)
      return ctx
        .answerCbQuery(`♻️ Объявление с ID ${ctx.match[1]} не найдено!`, true)
        .catch((err) => err);

    await items.destroy({
      where: {
        id: ctx.match[1],
      },
    });

    await ctx
      .answerCbQuery(
        `♻️ Объявление с ID ${ctx.match[1]} было успешно удалено!`,
        true
      )
      .catch((err) => err);

    await ctx.telegram.sendMessage(
      item.workerId,
      `<b>🤖 Администратор @${ctx.from.username} удалил объявление c ID </b><code>${item.id}</code>`,
      {
        parse_mode: "HTML",
      }
    );

    return require("./handlers/commands/admin/ads/list")(ctx);
  } catch (err) {
    console.log(err);
    try {
      return ctx.answerCbQuery(
        "🤖 Возникла ошибка при обработке данных пользователя!",
        true
      );
    } catch (err) {
      return ctx.replyWithHTML(
        "🤖 Возникла ошибка при обработке данных пользователя!"
      );
    }
  }
});

bot.action("admin_mentors_percent", async (ctx) => {
  return ctx.scene.enter("mentorPercent");
});
bot.action("admin_mentors", require("./handlers/commands/admin/mentors/index"));
bot.action(
  "admin_mentors_list",
  require("./handlers/commands/admin/mentors/list")
);
bot.action(
  /^admin_mentor_(\d+)$/,
  require("./handlers/commands/admin/mentors/mentor")
);
bot.action(
  /^admin_mentor_(\d+)_(changePercent|changeAbout|destroy)$/,
  async (ctx) => {
    try {
      const mentor = await Mentors.findOne({
        where: {
          id: ctx.match[1],
        },
      });

      if (ctx.match[2] == "destroy") {
        await Mentors.destroy({
          where: {
            id: ctx.match[1],
          },
        });

        await users.update(
          {
            status: 1,
          },
          {
            where: {
              id: mentor.workerId,
            },
          }
        );

        await users.update(
          {
            mentorId: null,
          },
          {
            where: {
              mentorId: mentor.workerId,
            },
          }
        );

        await ctx.answerCbQuery(`♻️ Наставник был успешно удален`);

        return require("./handlers/commands/admin/mentors/index")(ctx);
      } else if (ctx.match[2] == "changePercent") {
        return ctx.scene.enter("mentorChangePercent");
      } else {
        return ctx.scene.enter("mentorChangeAbout");
      }
    } catch (err) {
      console.log(err);
      return ctx
        .reply("🤖 Возникла ошибка при обработке данных пользователя!")
        .catch((err) => err);
    }
  }
);

bot.action("admin_domains", require("./handlers/commands/admin/domains/index"));
bot.action("admin_regru", require("./handlers/commands/admin/domains/regru"));
bot.action(
  "admin_domains_balance",
  require("./handlers/commands/admin/domains/balance")
);
bot.action("admin_domains_account", async (ctx) => {
  try {
    if (
      ctx.state.settings.regLogin == null &&
      ctx.state.settings.regPass == null
    ) {
      return ctx.scene.enter("addAccount");
    } else {
      return ctx.replyWithHTML(
        "⚠️ <b>У вас уже есть привязанный аккаунт!</b> Желаете его заменить?",
        {
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("➡️ Продолжить", "admin_domains_account2")],
            [Markup.callbackButton("♻️ Скрыть", "hide")],
          ]),
        }
      );
    }
  } catch (err) {
    console.log(err);
  }
});
bot.action("admin_domains_account2", async (ctx) => {
  return ctx.scene.enter("addAccount");
});
bot.action("admin_addDomain", async (ctx) => {
  return ctx.scene.enter("addDomain");
});
bot.action(
  "admin_allDomains",
  require("./handlers/commands/admin/domains/allDomains")
);
bot.action("admin_cf", async (ctx) => {
  try {
    if (
      ctx.state.settings.cfMail == null &&
      ctx.state.settings.cfId == null &&
      ctx.state.settings.cfApi == null
    ) {
      return ctx.scene.enter("addCf");
    } else {
      return ctx.replyWithHTML(
        "⚠️ <b>У вас уже есть привязанный аккаунт!</b> Желаете его заменить?",
        {
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("➡️ Продолжить", "admin_cf2")],
            [Markup.callbackButton("♻️ Скрыть", "hide")],
          ]),
        }
      );
    }
  } catch (err) {
    console.log(err);
  }
});
bot.action("admin_cf2", async (ctx) => {
  return ctx.scene.enter("addCf");
});
bot.action("admin_linkDomain", async (ctx) => {
  return ctx.scene.enter("linkDomain");
});
bot.action(
  /^admin_domain_(\d+)$/,
  require("./handlers/commands/admin/domains/domain")
);
bot.action(
  /^admin_domain_linked_(\d+)$/,
  require("./handlers/commands/admin/domains/linked")
);
bot.action(/^admin_domain_(\d+)_(spare|main)$/, async (ctx) => {
  try {
    const domain = await Domains.findOne({
      where: {
        id: ctx.match[1],
      },
    });

    if (domain.linked == false)
      return ctx.reply(
        "❌ Домен не привязан к серверу, ты не можешь отметить его как основной",
        {
          reply_markup: Markup.inlineKeyboard([
            [
              Markup.callbackButton(
                `🛡️ Привязать к серверу`,
                `admin_domain_linked_${domain.id}`
              ),
            ],
          ]),
        }
      );

    const Users = await users.findAndCountAll();

    const domains = await Domains.findAll();

    if (ctx.match[2] == "main") {
      await domains.map(
        async (v) =>
          await Domains.update(
            {
              status: false,
            },
            { where: { id: v.id } }
          )
      );

      await Promise.allSettled(
        Users.rows.map(
          async (v) =>
            await ctx.telegram
              .sendMessage(
                v.id,
                `🇪🇺 Администратор <a href="tg://user?id=${ctx.from.id}">${ctx.from.username}</a> сменил домен на сайтах. Можете продолжать работу по актуальным ссылкам!`,
                {
                  parse_mode: "HTML",
                  reply_markup: Markup.inlineKeyboard([
                    [Markup.callbackButton("♻️ Скрыть", "hide")],
                  ]),
                }
              )
              .catch((err) => err)
        )
      ).catch((err) => err);
    }

    await domain.update({
      status: ctx.match[2] == "spare" ? false : true,
    });

    const Services = await services.findAll();

    Services.map((v) =>
      services.update(
        {
          domain: `${v.sub}.${domain.domain}`,
        },
        { where: { code: v.code } }
      )
    );

    return require("./handlers/commands/admin/domains/allDomains")(ctx);
  } catch (er) {
    console.log(err);
    try {
      return ctx.answerCbQuery(
        "🤖 Возникла ошибка при обработке данных пользователя!",
        true
      );
    } catch (err) {
      return ctx.replyWithHTML(
        "🤖 Возникла ошибка при обработке данных пользователя!"
      );
    }
  }
});

bot.action("admin_changeDomain", async (ctx) => {
  return ctx.scene.enter("changeDomain");
});
bot.action("adminAlert", async (ctx) => {
  return ctx.scene.enter("adminAlert");
});

bot.action(
  /^request_(accept|decline)_(\d+)$/,
  require("./handlers/commands/admin/request")
);
bot.action(
  "admin_settings",
  require("./handlers/commands/admin/settings/index")
);
bot.action(
  /^mentor_(accept|decline)_(\d+)$/,
  require("./handlers/commands/admin/mentorRequest")
);

bot.action(/^user_(ban|unban)_(\d+)$/, async (ctx) => {
  try {
    const user = await users
      .findOne({
        where: {
          id: ctx.match[2],
        },
      })
      .catch((err) => err);

    await users
      .update(
        {
          banned: ctx.match[1] == "ban" ? true : false,
        },
        {
          where: {
            id: ctx.match[2],
          },
        }
      )
      .catch((err) => err);

    await ctx.editMessageReplyMarkup(
      Markup.inlineKeyboard([
        [
          Markup.callbackButton(
            `${ctx.match[1] == "ban" ? "🟢 Разбанить" : "🔴 Забанить"}`,
            `user_${ctx.match[1] == "ban" ? "unban" : "ban"}_${user.id}`
          ),
          Markup.callbackButton(
            "🛠 Изменить статус",
            `worker_status_${user.id}`
          ),
        ],
        // [Markup.callbackButton("💸 Профиты", `profit_user_${user.id}`)],
        [Markup.callbackButton("♻️ Скрыть", "hide")],
      ])
    );
    if (ctx.match[1] == "ban")
      return ctx.telegram
        .sendMessage(ctx.match[2], "❌ Вы были заблокированы в нашей тиме.")
        .catch((err) => err);
  } catch (err) {
    console.log(err);
  }
});

bot.action(/^(stop|full)Work$/, async (ctx) => {
  try {
    await ctx.state.settings.update({
      work: ctx.match[1] == "stop" ? false : true,
    });

    await ctx.answerCbQuery(
      `Статус проекта был изменен на ${
        ctx.match[1] == "stop" ? "❌ STOP WORK" : "✅ FULL WORK"
      }`
    );

    return require("./handlers/commands/admin/settings/index")(ctx);
  } catch (err) {
    console.log(err);
  }
});

bot.action(/^(off|work)(Sms|Mail|Domain|Ssl|Lk)$/, async (ctx) => {
  try {
    if (ctx.match[2] == "Sms") {
      await ctx.state.settings.update({
        sms: ctx.match[1] == "off" ? false : true,
      });
    } else if (ctx.match[2] == "Mail") {
      await ctx.state.settings.update({
        mail: ctx.match[1] == "off" ? false : true,
      });
    } else if (ctx.match[2] == "Domain") {
      await ctx.state.settings.update({
        domain: ctx.match[1] == "off" ? false : true,
      });
    } else if (ctx.match[2] == "Ssl") {
      await ctx.state.settings.update({
        sertSsl: ctx.match[1] == "off" ? false : true,
      });
    } else if (ctx.match[2] == "Lk") {
      await ctx.state.settings.update({
        lk: ctx.match[1] == "off" ? false : true,
      });
    }

    await ctx.answerCbQuery(
      `Статус ${ctx.match[2]} был изменен на ${
        ctx.match[1] == "off" ? "❌ STOP" : "✅ WORK"
      }`
    );

    return require("./handlers/commands/admin/settings/index")(ctx);
  } catch (err) {
    console.log(err);
  }
});

bot.hears(
  /^\/user @?([A-Za-z0-9_]+)$/,
  require("./handlers/commands/admin/users/index")
);
bot.action(
  /^admin_user_([A-Za-z0-9_]+)$/,
  require("./handlers/commands/admin/users/index")
);
bot.action(
  /^admin_profitsUser_(\d+)$/,
  require("./handlers/commands/admin/users/profits")
);
bot.action(
  /^admin_profits_user_(\d+)_(notpay|pay)$/,
  require("./handlers/commands/admin/users/profitsList")
);

bot.action(/^admin_userStatus_(\d+)$/, async (ctx) => {
  try {
    const id = ctx.match[1];

    const user = await users.findOne({
      where: {
        id: id,
      },
    });

    const profitsSum = parseFloat(
      await Profits.sum("eurAmount", {
        where: { workerId: user.id },
      })
    );

    return ctx
      .editMessageText(
        `<b>🗂️ Текущий раздел:</b>
╰ 🤖 Управление воркером -> Смена статуса

╭ ▫️ <b>Username:</b> <code>${ctx.from.first_name}</code>
├ ▫️ <b>User ID:</b> <code>${ctx.from.id}</code>
╰ ▫️ <b>Tag:</b> <code>#${ctx.state.user.tag}</code>
      
╭ 👤 <b>${
          user.admin == true
            ? "Администратор"
            : user.vbiver == true
            ? "Вбивер"
            : "Воркер"
        }:</b> @${user.username}
├ 💰 <b>Всего заработал:</b> € ${
          isNaN(profitsSum)
            ? "0"
            : ((profitsSum / 100) * user.percent).toFixed(2)
        }
├ 🏦 <b>Кошелек для выплаты:</b> <code>${
          user.wallet == null
            ? "Не установлен"
            : `<code>${user.wallet.split("&")[1]}</code> (${
                user.wallet.split("&")[0]
              })`
        }</code>
╰ #️⃣ <b>TAG:</b> <code>#${user.tag}</code>

├ 💁🏼‍♂️ <b>Текущий статус:</b> ${
          user.admin == true
            ? "Администратор"
            : user.vbiver == true
            ? "Вбивер"
            : "Воркер"
        }`,
        {
          parse_mode: "HTML",
          reply_markup: Markup.inlineKeyboard([
            [Markup.callbackButton("Воркер", `admin_setStatus_worker_${id}`)],
            [Markup.callbackButton("Вбивер", `admin_setStatus_writer_${id}`)],
            [
              Markup.callbackButton(
                "Администратор",
                `admin_setStatus_admin_${id}`
              ),
            ],
            [Markup.callbackButton("< Назад", `admin_user_${user.username}`)],
          ]),
        }
      )
      .catch((err) => err);
  } catch (err) {
    console.log(err);
    try {
      return ctx.answerCbQuery(
        "🤖 Возникла ошибка при обработке данных пользователя!",
        true
      );
    } catch (err) {
      return ctx.replyWithHTML(
        "🤖 Возникла ошибка при обработке данных пользователя!"
      );
    }
  }
});

bot.action(/^admin_setStatus_(worker|writer|admin)_(\d+)$/, async (ctx) => {
  try {
    const status = ctx.match[1];
    const id = ctx.match[2];
    const user = await users.findOne({ where: { id: id } });

    if (status == "worker") {
      await user.update({
        vbiver: false,
        admin: false,
        status: 1,
      });
    } else if (status == "writer") {
      await user.update({
        vbiver: true,
        admin: false,
        status: 1,
      });
    } else if (status == "admin") {
      await user.update({
        vbiver: false,
        admin: true,
        status: 1,
      });
    }
    await ctx.answerCbQuery(`✅ Статус успешно выдан`).catch((err) => err);
    await ctx.deleteMessage().catch((err) => err);
  } catch (err) {
    console.log(err);
    try {
      return ctx.answerCbQuery(
        "🤖 Возникла ошибка при обработке данных пользователя!",
        true
      );
    } catch (err) {
      return ctx.replyWithHTML(
        "🤖 Возникла ошибка при обработке данных пользователя!"
      );
    }
  }
});

module.exports = bot;