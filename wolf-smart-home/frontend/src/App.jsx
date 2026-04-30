import {Routes,Route,Link} from 'react-router-dom';import Dashboard from './pages/Dashboard';
export default function App(){return <div className='text-white min-h-screen p-4'><header className='flex justify-between'><h1>WOLF SMART HOME</h1><Link to='/'>Dashboard</Link></header><Routes><Route path='/' element={<Dashboard/>}/></Routes></div>}
