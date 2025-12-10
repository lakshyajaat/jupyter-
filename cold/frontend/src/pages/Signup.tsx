import React,{useState} from 'react';
import axios from 'axios';

export default function Signup(){
 const [name,setName]=useState('');
 const [email,setEmail]=useState('');
 const [password,setPassword]=useState('');

 const submit=async()=>{
  await axios.post('/auth/signup',{name,email,password});
  window.location.href='/';
 };

 return <div className='p-10'>
  <h1 className='text-2xl mb-4'>Signup</h1>
  <input className='border p-2' placeholder='name' onChange={e=>setName(e.target.value)}/>
  <input className='border p-2 ml-2' placeholder='email' onChange={e=>setEmail(e.target.value)}/>
  <input className='border p-2 ml-2' type='password' placeholder='password' onChange={e=>setPassword(e.target.value)}/>
  <button className='bg-green-500 text-white p-2 ml-2' onClick={submit}>Signup</button>
 </div>;
}
