const dotenv = require('dotenv');
dotenv.config();
module.exports = {
  port: process.env.PORT || 4000,
  mongoUri: process.env.MONGO_URI || 'mongodb://mongodb:27017/wolf',
  jwtSecret: process.env.JWT_SECRET || 'change-me',
  jwtRefreshSecret: process.env.JWT_REFRESH_SECRET || 'change-refresh',
  mqttUrl: process.env.MQTT_URL || 'mqtt://mqtt:1883',
  corsOrigin: process.env.CORS_ORIGIN || 'http://localhost:5173'
};
