import './App.css'
import Banner from './components/Banner.tsx'
import Panel from './components/Panel.tsx'
import VideoStream from './components/VideoStream.tsx'

function App() {
  return (
    <>
      <Banner/>
      <div className="top-section">
        <Panel></Panel>
        <VideoStream></VideoStream>
      </div>
      
    </>
  )
};

export default App
