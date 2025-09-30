const Sequelize = require("sequelize");

module.exports = function (sequelize) {
  return sequelize.define(
    "Services",
    {
      id: {
        type: Sequelize.INTEGER,
        primaryKey: true,
        autoIncrement: true
      },
      title: {
        type: Sequelize.TEXT,
      },
      sub: {
        type: Sequelize.TEXT,
      },
      code: {
        type: Sequelize.TEXT,
      },
      country: {
        type: Sequelize.TEXT,
      },
      currency: {
        type: Sequelize.TEXT,
      },
      domain: {
        type: Sequelize.TEXT,
      },
      work: {
        type: Sequelize.BOOLEAN,
      },
      status: {
        type: Sequelize.INTEGER,
      }
    },
    {
      timestamps: false,
    }
  );
};
