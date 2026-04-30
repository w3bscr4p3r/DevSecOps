const mongoose = require('mongoose');
const schema = new mongoose.Schema({
  name: String,email:{type:String,unique:true},password:String,phone:String,
  role:{type:String,enum:['admin','client'],default:'client'},active:{type:Boolean,default:true},
  plan:{type:String,enum:['SMART BASIC','SMART PLUS','EXECUTIVE'],default:'SMART BASIC'},
  refreshToken:String
},{timestamps:true});
module.exports = mongoose.model('User', schema);
