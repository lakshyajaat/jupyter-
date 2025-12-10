import React, { useState } from 'react';
import axios from 'axios';

export default function Login(){
 const [email,setEmail]=useState('');
 const [password,setPassword]=useState('');

 const submit=async()=>{
  const res=await axios.post('/auth/login',{email,password});
  localStorage.setItem('token',res.data.token);
  window.location.href='/dashboard';
 };

 return <div className='p-10'>
  <h1 className='text-2xl mb-4'>Login</h1>
  <input className='border p-2' placeholder='email' onChange={e=>setEmail(e.target.value)}/>
  <input className='border p-2 ml-2' type='password' placeholder='password' onChange={e=>setPassword(e.target.value)}/>
  <button className='bg-blue-500 text-white p-2 ml-2' onClick={submit}>Login</button>
 </div>;
}
