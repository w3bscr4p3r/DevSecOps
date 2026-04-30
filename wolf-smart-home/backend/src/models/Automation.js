const mongoose = require('mongoose');
module.exports = mongoose.model('Automation', new mongoose.Schema({homeId:{type:mongoose.Schema.Types.ObjectId,ref:'Home'},name:String,trigger:Object,action:Object,active:Boolean},{timestamps:true}));
