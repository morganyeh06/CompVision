import './VideoStream.css'
import Dropdown from './Dropdown';

export default function VideoStream() {
    const options = ["Firstname Lastname", "Lastname Firstname"]
    const resultText = "Time: 5.50\tPenalty: None\tFinal Result: 5.50";

    return (<>
        <div className="video-stream">
          <Dropdown name='curr-competitor' id='curr-competitor' text='Current Competitor' options={options} direction='row'></Dropdown>
          <img src="http://127.0.0.1:8000/video_feed" alt="Live Camera Feed" className="live-feed"></img>
          <div className="result">{resultText}</div>
        </div>
    </>);
};