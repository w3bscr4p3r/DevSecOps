const r=require('express').Router();const auth=require('../middlewares/auth');const rbac=require('../middlewares/rbac');const M=require('../models/Payment');const f=require('./crudFactory')(M);
r.get('/',auth,f.list);r.post('/',auth,rbac('admin'),f.create);module.exports=r;
