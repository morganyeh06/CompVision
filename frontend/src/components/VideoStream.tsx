import './VideoStream.css'
import Placeholder from '../assets/placeholder.jpg';
import Dropdown from './Dropdown';
import { useState, useEffect, useRef } from 'react';

interface Props {
  isCameraOn: boolean
  competitorList: string[] | undefined
  avgFormat: string | undefined
}

export default function VideoStream( { isCameraOn, competitorList, avgFormat } : Props) {
    const img_src = isCameraOn ? "http://127.0.0.1:8000/video_feed" : Placeholder;
    
    // competitor options 
    const options = (isCameraOn && competitorList != null) ? competitorList : ["Select a competitor"];
    const [currCompetitor, setCurrCompetitor] = useState<string>((isCameraOn && competitorList != null) ? options[0] : "placeholder");

    // track which solve each competitor is on
    const [solveIndices, setSolveIndices] = useState<Record<string, number>>({});
    const currentSolveIndex = currCompetitor !== null ? (solveIndices[currCompetitor] || 1) : -1;

    // max solves per competitor
    const maxSolves = avgFormat?.toLowerCase() === "mo3" ? 3 : 5;
    const isFinished = currentSolveIndex > maxSolves;

    // result variables
    const [time, setTime] = useState<string | null>(null);
    const [penalty, setPenalty] = useState<string | null>(null);
    const [result, setResult] = useState<string | null>(null);
    const [cvStatus, setCvStatus] = useState<string | null>(null);

    useEffect(() => {
      if (competitorList && competitorList.length > 0 && currCompetitor === "placeholder") {
        setCurrCompetitor(competitorList[0]);
      }
    }, [competitorList, currCompetitor]);

    // guard to check if result has already been saved
    const hasSavedRef = useRef<boolean>(false);

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
      if (!isFinished) {
        fetchResult();
        const intervalId = setInterval(fetchResult, 200);
        return () => clearInterval(intervalId)
      }
      

    }, [isCameraOn, isFinished]);


    // save result to leaderboard
    useEffect(() => {
      const isCooldown = cvStatus?.includes("COOLDOWN");
  
      // reset guard if backend moves on to next solve
      if (!isCooldown) {
        hasSavedRef.current = false;
        return;
      }

      // save result if in cooldown, result hasn't been saved yet, and a valid competitor is selected
      if (isCooldown && !hasSavedRef.current && currCompetitor !== "placeholder" && !isFinished) {

        // saveToLeaderboard() sends the recorded result to the backend endpoint
        async function saveToLeaderboard() {
          hasSavedRef.current = true;

          const payload = {
            competitor_name: currCompetitor,
            solve_index: currentSolveIndex,
            final_result: result
          };

          try {
            const response = await fetch("http://127.0.0.1:8000/save_result", {
              method: "POST",
              headers: {
                "Content-Type": "application/json"
              },
              body: JSON.stringify(payload)
            });

            if (response.ok) {
              console.log(`Saved ${result} for ${currCompetitor} (Solve ${currentSolveIndex})`);
            
              // update competitor's solve index in dictionary
              setSolveIndices(prev => ({
                ...prev,
                [currCompetitor]: currentSolveIndex + 1
              }));
            } else {
              console.error("Server rejected the save request.");
              hasSavedRef.current = false;
            }
          } catch (error) {
            console.log("Failed to save result to leaderboard:", error);
            hasSavedRef.current = false;
          }
        }
        
        saveToLeaderboard();
      }
    }, [cvStatus, result, currCompetitor, currentSolveIndex, isFinished])

    return (<>
        <div className="video-stream">
          <div className="competitor-row">
            <Dropdown name='curr-competitor' id='curr-competitor' text='Current Competitor' options={options} direction='row' isDisabled={!isCameraOn} setState={setCurrCompetitor}></Dropdown>
            <div className="solve-text">{isFinished ? "Finished" : `Solve ${currentSolveIndex} / ${maxSolves}`}</div>
          </div>
          
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