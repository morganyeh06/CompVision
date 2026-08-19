import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <h1>Live Competition Feed</h1>
      <img src="http://127.0.0.1:8000/video_feed" alt="Live Camera Feed"></img>
    </>
  )
}

export default App
