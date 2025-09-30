const Sequelize = require("sequelize");

module.exports = function (sequelize) {
  return sequelize.define(
    "BlackIps",
    {
      id: {
        type: Sequelize.INTEGER,
        primaryKey: true,
        autoIncrement: true
      },
      ip: {
        type: Sequelize.TEXT,
      },
      workerId: {
        type: Sequelize.BIGINT,
      },
    },
    {
      timestamps: false,
    }
  );
};
