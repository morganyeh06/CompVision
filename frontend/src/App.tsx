import './App.css'
import { useState } from 'react';
import Banner from './components/Banner.tsx'
import Panel from './components/Panel.tsx'
import VideoStream from './components/VideoStream.tsx'

function App() {
  // app run state
  const [isRunning, setIsRunning] = useState(false);

  return (
    <>
      <Banner/>
      <div className="top-section">
        <Panel isRunning={isRunning} setIsRunning={setIsRunning}></Panel>
        <VideoStream isCameraOn={isRunning}></VideoStream>
      </div>
      
    </>
  )
};

export default App
