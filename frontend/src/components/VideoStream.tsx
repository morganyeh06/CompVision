import './VideoStream.css'
import Placeholder from '../assets/placeholder.jpg';
import Dropdown from './Dropdown';

interface Props {
  isCameraOn: boolean
}

export default function VideoStream( { isCameraOn } : Props) {
    const img_src = isCameraOn ? "http://127.0.0.1:8000/video_feed" : Placeholder;
    
    // TODO: get values from backend
    const options = ["Firstname Lastname", "Lastname Firstname"]
    const time = '45.67';
    const penalty = '+2';
    const result = '47.67';

    return (<>
        <div className="video-stream">
          <Dropdown name='curr-competitor' id='curr-competitor' text='Current Competitor' options={options} direction='row'></Dropdown>
          <img src={img_src} alt="Live Camera Feed" className="live-feed"></img>
          <div className="result-container">
            <div className="result-text" id='time'>Time: {time}</div>
            <div className='result-text' id='penalty'>Penalty: {penalty}</div>
            <div className='result-text' id='final-result'>Result: {result}</div>
          </div>
          
        </div>
    </>);
};