module.exports = (Model)=>({
  list: async (_,res)=>res.json(await Model.find()),
  create: async (req,res)=>res.status(201).json(await Model.create(req.body)),
  update: async (req,res)=>res.json(await Model.findByIdAndUpdate(req.params.id, req.body, {new:true})),
  remove: async (req,res)=>res.json(await Model.findByIdAndDelete(req.params.id))
});
