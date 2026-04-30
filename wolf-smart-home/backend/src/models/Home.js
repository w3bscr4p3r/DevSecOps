const mongoose = require('mongoose');
module.exports = mongoose.model('Home', new mongoose.Schema({ownerId:{type:mongoose.Schema.Types.ObjectId,ref:'User'},address:String,city:String,state:String,devices:[{type:mongoose.Schema.Types.ObjectId,ref:'Device'}],plan:String},{timestamps:true}));
