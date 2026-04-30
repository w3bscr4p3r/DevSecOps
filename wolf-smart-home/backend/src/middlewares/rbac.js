module.exports = (...roles)=>(req,res,next)=> roles.includes(req.user.role)?next():res.status(403).json({message:'Acesso negado'});
