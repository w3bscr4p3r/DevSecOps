const mongoose = require('mongoose');
module.exports = mongoose.model('SensorLog', new mongoose.Schema({deviceId:{type:mongoose.Schema.Types.ObjectId,ref:'Device'},temperature:Number,humidity:Number,power:Number,timestamp:{type:Date,default:Date.now}}));
