import './App.css'
import { useState, useEffect } from 'react';
import Banner from './components/Banner.tsx'
import Panel from './components/Panel.tsx'
import { type CompSettings } from './components/Panel.tsx';
import VideoStream from './components/VideoStream.tsx'
import Leaderboard from './components/Leaderboard.tsx';

export const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  // app states
  const [isBackendReady, setIsBackendReady] = useState<boolean>(false);
  const [isRunning, setIsRunning] = useState(false);
  const [currentSettings, setCurrentSettings] = useState<CompSettings | null>(null);

  function handleSettingsSaved(settings: CompSettings) {
    setCurrentSettings(settings);
  }

  // checks if backend is ready
  useEffect(() => {
    // checkBackend() checks if the backend has finished booting up
     async function checkBackend() {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 500);
  
        const res = await fetch(`${API_URL}/backend_status`, { 
          signal: controller.signal,
          cache: 'no-store' 
        });
            
        clearTimeout(timeoutId);
        setIsBackendReady(res.ok ? true : false)
          
      } catch (error) {
        setIsBackendReady(false);
      }
    }
  
    checkBackend();
    const interval = setInterval(checkBackend, 1000);
    return () => clearInterval(interval)
  }, []);

  return (
    <>
      <Banner/>
      <div className="top-section">
        <Panel isRunning={isRunning} isBackendReady={isBackendReady} setIsRunning={setIsRunning} saveSettings={handleSettingsSaved}></Panel>
        <VideoStream isRunning={isRunning} isBackendReady={isBackendReady} competitorList={currentSettings?.competitors} avgFormat={currentSettings?.avg_format}></VideoStream>
      </div>
      {isRunning ?
        <Leaderboard avgFormat={currentSettings?.avg_format} event={currentSettings?.event} round={currentSettings?.round_number}></Leaderboard>
      : null}
    </>
  )
};

export default App
