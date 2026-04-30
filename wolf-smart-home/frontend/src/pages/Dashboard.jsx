import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';
const data=[{t:'18:00',temp:24},{t:'19:00',temp:25},{t:'20:00',temp:23}];
export default function Dashboard(){return <div className='grid gap-4 mt-6'><motion.div initial={{opacity:0}} animate={{opacity:1}} className='bg-slate-900 p-4 rounded-2xl'>Online: 14 | Alarmes: 0</motion.div><div className='bg-slate-900 p-4 rounded-2xl h-64'><ResponsiveContainer><LineChart data={data}><XAxis dataKey='t'/><YAxis/><Tooltip/><Line type='monotone' dataKey='temp' stroke='#d4af37'/></LineChart></ResponsiveContainer></div></div>}
