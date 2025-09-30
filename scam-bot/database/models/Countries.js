const Sequelize = require("sequelize");

module.exports = function (sequelize) {
  return sequelize.define(
    "Countries",
    {
      id: {
        type: Sequelize.INTEGER,
        primaryKey: true,
        autoIncrement: true
      },
      title: {
        type: Sequelize.TEXT,
      },
      code: {
        type: Sequelize.TEXT,
      },
      work: {
        type: Sequelize.BOOLEAN,
      },
      lk: {
        type: Sequelize.BOOLEAN,
      }
    },
    {
      timestamps: false,
    }
  );
};
