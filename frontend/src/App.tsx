import './App.css'
import { useState } from 'react';
import Banner from './components/Banner.tsx'
import Panel from './components/Panel.tsx'
import { type CompSettings } from './components/Panel.tsx';
import VideoStream from './components/VideoStream.tsx'

function App() {
  // app states
  const [isRunning, setIsRunning] = useState(false);
  const [currentSettings, setCurrentSettings] = useState<CompSettings | null>(null);

  function handleSettingsSaved(settings: CompSettings) {
    setCurrentSettings(settings);
  }

  return (
    <>
      <Banner/>
      <div className="top-section">
        <Panel isRunning={isRunning} setIsRunning={setIsRunning} saveSettings={handleSettingsSaved}></Panel>
        <VideoStream isCameraOn={isRunning} competitorList={currentSettings?.competitors} avgFormat={currentSettings?.avg_format}></VideoStream>
      </div>
      
    </>
  )
};

export default App
