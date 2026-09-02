import './App.css'
import { useState } from 'react';
import Banner from './components/Banner.tsx'
import Panel from './components/Panel.tsx'
import { type CompSettings } from './components/Panel.tsx';
import VideoStream from './components/VideoStream.tsx'
import Leaderboard from './components/Leaderboard.tsx';

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
        <VideoStream isRunning={isRunning} competitorList={currentSettings?.competitors} avgFormat={currentSettings?.avg_format}></VideoStream>
      </div>
      {isRunning ?
        <Leaderboard avgFormat={currentSettings?.avg_format} event={currentSettings?.event} round={currentSettings?.round_number}></Leaderboard>
      : null}
    </>
  )
};

export default App
