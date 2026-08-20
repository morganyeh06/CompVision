import './App.css';
import Banner from './components/Banner.tsx';

function App() {
  return (
    <>
      <Banner/>
      <h1>Live Competition Feed</h1>
      <img src="http://127.0.0.1:8000/video_feed" alt="Live Camera Feed"></img>
    </>
  )
};

export default App
