const Sequelize = require("sequelize");

module.exports = function (sequelize) {
  return sequelize.define(
    "Domains",
    {
      id: {
        type: Sequelize.INTEGER,
        primaryKey: true,
        autoIncrement: true
      },
      domain: {
        type: Sequelize.TEXT,
      },
      status: {
        type: Sequelize.BOOLEAN,
      },
      linked: {
        type: Sequelize.BOOLEAN,
      }
    },
    {
      timestamps: false,
    }
  );
};
