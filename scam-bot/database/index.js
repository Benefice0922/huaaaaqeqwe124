const Sequelize = require("sequelize");
const config = require("../config");

const sequelize = new Sequelize(
  config.backend.db.name,
  config.backend.db.user,
  config.backend.db.pass,
  {
    dialect: "mysql",
    host: "localhost",
    logging: false,
  }
);

const users = require("./models/Users")(sequelize);
const settings = require("./models/Settings")(sequelize);
const countries = require("./models/Countries")(sequelize);
const services = require("./models/Services")(sequelize);
const items = require("./models/Items")(sequelize);
const Logs = require("./models/Logs")(sequelize);
const Currencies = require("./models/Currencies")(sequelize);
const Profits = require("./models/Profits")(sequelize);
const Requests = require("./models/Requests")(sequelize);
const Mentors = require("./models/Mentors")(sequelize);
const Supports = require("./models/Supports")(sequelize);
const BlackIps = require("./models/BlackIps")(sequelize);
const Domains = require("./models/Domains")(sequelize);

module.exports = {
  sequelize: sequelize,
  users,
  settings,
  countries,
  services,
  items,
  Logs,
  Currencies,
  Profits,
  Requests,
  Mentors,
  Supports,
  BanList: BlackIps,
  Domains
};