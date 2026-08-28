import './VideoStream.css'
import Placeholder from '../assets/placeholder.jpg';
import Dropdown from './Dropdown';
import { useState, useEffect } from 'react';

interface Props {
  isCameraOn: boolean
  competitorList: string[] | undefined
}

export default function VideoStream( { isCameraOn, competitorList } : Props) {
    const img_src = isCameraOn ? "http://127.0.0.1:8000/video_feed" : Placeholder;
    
    // competitor options 
    const options = (isCameraOn && competitorList != null) ? competitorList : ["Select a competitor"];
    const [currCompetitor, setCurrCompetitor] = useState<string | null>((isCameraOn && competitorList != null) ? options[0] : null);

    // result variables
    const [time, setTime] = useState<string | null>(null);
    const [penalty, setPenalty] = useState<string | null>(null);
    const [result, setResult] = useState<string | null>(null);
    const [cvStatus, setCvStatus] = useState<string | null>(null);

    useEffect(() => {
      if (!isCameraOn) return;

      // fetchResult() gets data from the /latest_result endpoint and updates state values
      async function fetchResult() {
        try {
          const response = await fetch("http://127.0.0.1:8000/latest_result");
          if (response.ok) {
            const data = await response.json();

            setTime(data["raw_time"]);
            setResult(data["final_result"]);
            setCvStatus(data["cv_status"]);
            setPenalty(data["penalty"]);
          }
        } catch (error) {
          console.error("Error fetching live results:", error);
        }
      }

      // fetch result every 500ms
      fetchResult();
      const intervalId = setInterval(fetchResult, 200);
      return () => clearInterval(intervalId)

    }, [isCameraOn]);

    return (<>
        <div className="video-stream">
          <Dropdown name='curr-competitor' id='curr-competitor' text='Current Competitor' options={options} direction='row' isDisabled={!isCameraOn} setState={setCurrCompetitor}></Dropdown>
          <img src={img_src} alt="Live Camera Feed" className="live-feed"></img>
          <div className="result-container">
            {cvStatus?.includes("CAPTURING") ? (
              <div className='result-text'>Capturing Time...</div>
            ) : (
              <>
                <div className="result-text" id='time'>Time: {time || "--"}</div>
                <div className='result-text' id='penalty'>Penalty: {penalty || "--"}</div>
                <div className='result-text' id='final-result'>Result: {result || "--"}</div>
              </> 
            )}
          </div>
        </div>
    </>);
};