import './VideoStream.css'
import Placeholder from '../assets/placeholder.jpg';
import Dropdown from './Dropdown';
import { useState, useEffect, useRef } from 'react';

interface Props {
  isRunning: boolean
  competitorList: string[] | undefined
  avgFormat: string | undefined
}

interface CompetitorData {
  name: string;
  solves: string[];
}

export default function VideoStream( { isRunning, competitorList, avgFormat } : Props) {
    const img_src = "http://127.0.0.1:8000/video_feed";
    
    // competitor options 
    const options = (isRunning && competitorList != null) ? competitorList : ["Select a competitor"];
    const [currCompetitor, setCurrCompetitor] = useState<string>((isRunning && competitorList != null) ? options[0] : "placeholder");

    // track each competitors' solves
    const [leaderboardData, setLeaderboardData] = useState<CompetitorData[]>([]);

    // max solves per competitor
    const maxSolves = avgFormat?.toLowerCase() === "mo3" ? 3 : 5;

    // current solve index is always leftmost empty index
    let currentSolveIndex = 1;
    if (isRunning && currCompetitor !== "placeholder") {
      // get data for current competitor
      const compData = leaderboardData.find(c => c.name === currCompetitor);

      if (compData && compData.solves) {
        // find leftmost empty index
        const emptyIndex = compData.solves.findIndex(s => s === "");
        currentSolveIndex = (emptyIndex !== -1) ? emptyIndex + 1 : maxSolves + 1;
      }
    }

    const isFinished = isRunning && currentSolveIndex > maxSolves;

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
      if (!isRunning) return;

      // fetchResult() gets data from the /latest_result and /leaderboard endpoints
      async function fetchResult() {
        try {
          // simultaneously fetch data from both endpoints
          const [cvRes, boardRes] = await Promise.all([
            fetch("http://127.0.0.1:8000/latest_result", { cache: 'no-store' }),
            fetch("http://127.0.0.1:8000/leaderboard", { cache: 'no-store' })
          ]);

          if (cvRes.ok) {
            const data = await cvRes.json();

            setTime(data["raw_time"]);
            setResult(data["final_result"]);
            setCvStatus(data["cv_status"]);
            setPenalty(data["penalty"]);
          }

          if (boardRes.ok) {
            const boardData = await boardRes.json();
            setLeaderboardData(boardData.leaderboard);
          }
        } catch (error) {
          console.error("Error fetching live results:", error);
        }
      }

      // fetch result every 500ms
      fetchResult();
      const intervalId = setInterval(fetchResult, 200);
      return () => clearInterval(intervalId)

    }, [isRunning, currCompetitor]);


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
    }, [cvStatus, result, currCompetitor, currentSolveIndex, isFinished]);

    // reset time, penalty, result when competitor changes
    useEffect(() => {
      setTime(null);
      setPenalty(null);
      setResult(null);

      if (currCompetitor !== "placeholder") {
        try {
          fetch("http://127.0.0.1:8000/reset_cv", { "method": "POST"})
        } catch(error) {
          console.error("Failed to reset backend CV state: ", error)
        }
      }
    }, [currCompetitor]);


    return (<>
        <div className="video-stream">
          <div className="competitor-row">
            <Dropdown name='curr-competitor' id='curr-competitor' text='Current Competitor' options={options} direction='row' isDisabled={!isRunning} setState={setCurrCompetitor}></Dropdown>
            <div className="solve-text">{isFinished ? "Finished" : `Solve ${!isRunning ? "-" : currentSolveIndex} / ${maxSolves}`}</div>
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