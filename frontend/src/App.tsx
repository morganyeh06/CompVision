import './App.css'
import Banner from './components/Banner.tsx'
import Panel from './components/Panel.tsx'

function App() {
  return (
    <>
      <Banner/>
      <div className="top-section">
        <Panel></Panel>
        <div className="live-feed">
          <h1>Live Competition Feed</h1>
          <img src="http://127.0.0.1:8000/video_feed" alt="Live Camera Feed"></img>
        </div>
      </div>
      
    </>
  )
};

export default App
