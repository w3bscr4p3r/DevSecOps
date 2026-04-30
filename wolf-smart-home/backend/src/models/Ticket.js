const mongoose = require('mongoose');
module.exports = mongoose.model('Ticket', new mongoose.Schema({userId:{type:mongoose.Schema.Types.ObjectId,ref:'User'},subject:String,priority:String,status:String,messages:[{author:String,body:String,at:{type:Date,default:Date.now}}]},{timestamps:true}));
