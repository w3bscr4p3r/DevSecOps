const jwt = require('jsonwebtoken');
const { jwtSecret } = require('../config/env');
module.exports = (req,res,next)=>{const h=req.headers.authorization||'';const t=h.replace('Bearer ','');if(!t)return res.status(401).json({message:'Sem token'});try{req.user=jwt.verify(t,jwtSecret);next();}catch{return res.status(401).json({message:'Token inválido'});}};
