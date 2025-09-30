const Sequelize = require("sequelize");

module.exports = function (sequelize) {
  return sequelize.define(
    "Requests",
    {
      id: {
        type: Sequelize.INTEGER,
        primaryKey: true,
        autoIncrement: true
      },
      workerId: {
        type: Sequelize.BIGINT,
      },
      question1: {
        type: Sequelize.TEXT,
      },
      question2: {
        type: Sequelize.TEXT,
      },
      question3: {
        type: Sequelize.TEXT,
      },
      status: {
        type: Sequelize.BOOLEAN,
      }
    },
    {
      timestamps: false,
    }
  );
};
