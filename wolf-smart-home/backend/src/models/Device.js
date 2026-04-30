const mongoose = require('mongoose');
module.exports = mongoose.model('Device', new mongoose.Schema({homeId:{type:mongoose.Schema.Types.ObjectId,ref:'Home'},name:String,type:String,topic:String,status:String,online:Boolean,lastSeen:Date,firmwareVersion:String},{timestamps:true}));
