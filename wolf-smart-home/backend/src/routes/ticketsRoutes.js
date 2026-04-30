const r=require('express').Router();const auth=require('../middlewares/auth');const M=require('../models/Ticket');const f=require('./crudFactory')(M);
r.get('/',auth,f.list);r.post('/',auth,f.create);r.put('/:id',auth,f.update);module.exports=r;
