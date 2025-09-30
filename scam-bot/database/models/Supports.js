const Sequelize = require("sequelize");

module.exports = function (sequelize) {
  return sequelize.define(
    "Supports",
    {
      id: {
        type: Sequelize.INTEGER,
        primaryKey: true,
        autoIncrement: true
        },
      itemId: {
        type: Sequelize.TEXT,
      },
      text: {
        type: Sequelize.TEXT,
      },
      who: {
        type: Sequelize.TEXT,
      },
      readed: {
        type: Sequelize.BOOLEAN,
      },
    },
    {
      timestamps: false,
    }
  );
};
