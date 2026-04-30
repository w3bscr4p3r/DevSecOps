const mongoose = require('mongoose');
module.exports = mongoose.model('Payment', new mongoose.Schema({userId:{type:mongoose.Schema.Types.ObjectId,ref:'User'},amount:Number,status:String,dueDate:Date,paidAt:Date},{timestamps:true}));
