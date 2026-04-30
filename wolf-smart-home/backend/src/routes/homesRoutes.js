const r=require('express').Router();const auth=require('../middlewares/auth');const Home=require('../models/Home');const f=require('./crudFactory')(Home);
r.get('/',auth,f.list);r.post('/',auth,f.create);r.put('/:id',auth,f.update);r.delete('/:id',auth,f.remove);module.exports=r;
