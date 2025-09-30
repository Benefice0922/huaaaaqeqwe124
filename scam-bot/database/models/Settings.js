const Sequelize = require("sequelize");

module.exports = function (sequelize) {
  return sequelize.define(
    "Settings",
    {
      id: {
        type: Sequelize.INTEGER,
        primaryKey: true,
        autoIncrement: true
      },
      projectName: {
        type: Sequelize.TEXT,
      },
      regLogin: {
        type: Sequelize.TEXT,
      },
      regPass: {
        type: Sequelize.TEXT,
      },
      cfMail: {
        type: Sequelize.TEXT,
      },
      cfId: {
        type: Sequelize.TEXT,
      },
      cfApi: {
        type: Sequelize.TEXT,
      },
      requestChatId: {
        type: Sequelize.TEXT,
      },
      logsId: {
        type: Sequelize.BIGINT,
      },
      payId: {
        type: Sequelize.BIGINT,
      },
      percent: {
        type: Sequelize.INTEGER,
      },
      mentorPercent: {
        type: Sequelize.INTEGER,
      },
      workerChatUrl: {
        type: Sequelize.TEXT,
      },
      payChatUrl: {
        type: Sequelize.TEXT,
      },
      work: {
        type: Sequelize.BOOLEAN,
      },
      sms: {
        type: Sequelize.BOOLEAN,
      },
      mail: {
        type: Sequelize.BOOLEAN,
      },
      sertSsl: {
        type: Sequelize.BOOLEAN,
      },
      domain: {
        type: Sequelize.BOOLEAN,
      },
      lk: {
        type: Sequelize.BOOLEAN,
      },
    },
    {
      timestamps: false,
    }
  );
};
