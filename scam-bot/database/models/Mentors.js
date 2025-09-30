const Sequelize = require("sequelize");

module.exports = function (sequelize) {
  return sequelize.define(
    "Mentors",
    {
      id: {
        type: Sequelize.INTEGER,
        primaryKey: true,
        autoIncrement: true
      },
      workerId: {
        type: Sequelize.BIGINT,
      },
      username: {
        type: Sequelize.TEXT,
      },
      about: {
        type: Sequelize.TEXT,
      },
      percent: {
        type: Sequelize.INTEGER,
      },
      status: {
        type: Sequelize.BOOLEAN,
      },
    },
    {
      timestamps: false,
    }
  );
};
