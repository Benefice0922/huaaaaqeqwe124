const Sequelize = require("sequelize");

module.exports = function (sequelize) {
  return sequelize.define(
    "Items",
    {
      id: {
        type: Sequelize.TEXT,
        primaryKey: true,
      },
      cardMsgId: {
        type: Sequelize.TEXT,
      },
      workerId: {
        type: Sequelize.BIGINT,
      },
      title: {
        type: Sequelize.TEXT,
      },
      photo: {
        type: Sequelize.TEXT,
      },
      price: {
        type: Sequelize.TEXT,
      },
      address: {
        type: Sequelize.TEXT
      },
      name: {
        type: Sequelize.TEXT,
      },
      currency: {
        type: Sequelize.TEXT,
      },
      serviceCode: {
        type: Sequelize.TEXT,
      },
      status: {
        type: Sequelize.INTEGER,
      },
      chatStatus: {
        type: Sequelize.INTEGER,
      },
      online: {
        type: Sequelize.BOOLEAN,
      },
      msgId: {
        type: Sequelize.TEXT,
      },
      // НОВЫЕ ПОЛЯ ДЛЯ ДАННЫХ ПОЛУЧАТЕЛЯ
      receiverName: {
        type: Sequelize.STRING,
        allowNull: true
      },
      receiverPhone: {
        type: Sequelize.STRING,
        allowNull: true
      },
      receiverAddress: {
        type: Sequelize.TEXT,
        allowNull: true
      }
    },
    {
      timestamps: false,
    }
  );
};