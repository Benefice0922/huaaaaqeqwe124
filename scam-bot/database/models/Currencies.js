const Sequelize = require("sequelize");

module.exports = function (sequelize) {
  return sequelize.define(
    "Currencies",
    {
      id: {
        type: Sequelize.INTEGER,
        primaryKey: true,
        autoIncrement: true
      },
      symbol: {
        type: Sequelize.TEXT,
      },
      displayed: {
        type: Sequelize.TEXT,
      }
    },
    {
      timestamps: false,
    }
  );
};
