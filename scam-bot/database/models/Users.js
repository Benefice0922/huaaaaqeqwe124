const Sequelize = require("sequelize");

module.exports = function (sequelize) {
  return sequelize.define(
    "Users",
    {
      id: {
        type: Sequelize.BIGINT,
        primaryKey: true,
      },
      username: {
        type: Sequelize.TEXT,
      },
      tag: {
        type: Sequelize.TEXT,
      },
      wallet: {
        type: Sequelize.TEXT,
      },
      profitSum: {
        type: Sequelize.INTEGER,
      },
      mentorId: {
        type: Sequelize.BIGINT,
      },
      status: {
        type: Sequelize.INTEGER
      },
      admin: {
        type: Sequelize.BOOLEAN
      },
      vbiver: {
        type: Sequelize.BOOLEAN
      },
      banned: {
        type: Sequelize.BOOLEAN
      },
      percent: {
        type: Sequelize.INTEGER,
      },
      address: {
        type: Sequelize.TEXT
      },
      name: {
        type: Sequelize.TEXT,
      },
      siteStatus: {
        type: Sequelize.BOOLEAN
      },
      supportType: {
        type: Sequelize.TEXT(255)
      }
    },
    {
      timestamps: false,
    }
  );
};
