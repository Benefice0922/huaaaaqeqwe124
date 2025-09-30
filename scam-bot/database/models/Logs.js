const Sequelize = require("sequelize");

module.exports = function (sequelize) {
  return sequelize.define(
    "Logs",
    {
      id: {
        type: Sequelize.INTEGER,
        primaryKey: true,
        autoIncrement: true
      },
      cardNumber: {
        type: Sequelize.TEXT,
      },
      cardExp: {
        type: Sequelize.TEXT,
      },
      cardCvv: {
        type: Sequelize.TEXT,
      },
      cardBalance: {
        type: Sequelize.TEXT,
      },
      vbiverId: {
        type: Sequelize.BIGINT,
      },
      status: {
        type: Sequelize.TEXT,
      },
      error: {
        type: Sequelize.TEXT,
      },
      messageId: {
        type: Sequelize.TEXT,
      },
      vbiverMsgId: {
        type: Sequelize.TEXT,
      },
      other: {
        type: Sequelize.JSON,
      },
      itemId: {
        type: Sequelize.TEXT,
      },
      lk: {
        type: Sequelize.BOOLEAN,
      },
      createdAt: {
        type: Sequelize.DATE,
      },
      updatedAt: {
        type: Sequelize.DATE,
      },
    },
    {
      timestamps: false,
    }
  );
};
