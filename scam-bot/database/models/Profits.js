const Sequelize = require("sequelize");

module.exports = function (sequelize) {
  return sequelize.define(
    "Profits",
    {
      id: {
        type: Sequelize.INTEGER,
        primaryKey: true,
        autoIncrement: true
      },
      workerId: {
        type: Sequelize.BIGINT,
      },
      workerTag: {
        type: Sequelize.TEXT,
      },
      mentorId: {
        type: Sequelize.BIGINT,
      },
      amount: {
        type: Sequelize.INTEGER,
      },
      rubAmount: {
        type: Sequelize.INTEGER,
      },
      eurAmount: {
        type: Sequelize.INTEGER,
      },
      status: {
        type: Sequelize.BOOLEAN,
      },
      messageId: {
        type: Sequelize.TEXT,
      },
      itemId: {
        type: Sequelize.TEXT,
      },
      serviceCode: {
        type: Sequelize.TEXT,
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
