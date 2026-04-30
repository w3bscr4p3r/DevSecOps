const mongoose = require('mongoose');
const { mongoUri } = require('./env');
module.exports = async function connectDb() {
  await mongoose.connect(mongoUri);
  console.log('MongoDB conectado');
};
