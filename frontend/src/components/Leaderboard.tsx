import { useState, useEffect } from 'react';
import './Leaderboard.css';

interface CompetitorResult {
    rank: number | string;
    name: string;
    solves: string[];
    best: string;
    average: string;
    is_finished: boolean;
}

interface Props {
    avgFormat: string | undefined;
    event: string | undefined;
    round: string | undefined;
}

export default function Leaderboard({ avgFormat, event, round }: Props) {
    const [leaderboard, setLeaderboard] = useState<CompetitorResult[]>([])
    const isFormatMo3 = avgFormat?.toLowerCase() === "mo3";
    const numSolves = isFormatMo3 ? 3 : 5;
    const avgColName = isFormatMo3 ? "Mean" : "Average";

    useEffect(() => {
        async function fetchLeaderboard() {
            try {
                const response = await fetch("http://127.0.0.1:8000/leaderboard");
                if (response.ok) {
                    const data = await response.json();
                    setLeaderboard(data.leaderboard);
                }
            } catch(error) {
                console.error("Failed to fetch leaderboard,", error);
            }
        }

        // fetch leaderboard every second
        fetchLeaderboard();
        const interval = setInterval(fetchLeaderboard, 1000);
        return () => clearInterval(interval);
    }, []);

    return (
    <div className="leaderboard">
      <h5 className="leaderboard-title">{event} - Round {round}</h5>
      
      <div className="shadow-sm">
        <table className="table">
          <thead className="table-light text-muted">
            <tr>
              <th className="rank-col text-end">#</th>
              <th className="name-col text-start">Name</th>
              {/* create solve number columns */}
              {Array.from({ length: numSolves }, (_, i) => (
                <th className="time-col text-end" key={i}>{i + 1}</th>
              ))}
              <th className="time-col text-end">{avgColName}</th>
              <th className="time-col text-end">Best</th>
            </tr>
          </thead>
          
          <tbody>
            {leaderboard.map((comp, idx) => {
              // green for finished, yellow for ongoing
              const rowStyle = comp.is_finished 
                ? { backgroundColor: '#00d65f', color: 'black' } 
                : { backgroundColor: '#ffd500', color: 'black' };

              return (
                <tr key={idx}>
                  <td className="text-end" style={rowStyle}>{comp.rank}</td>
                  <td className="name-col text-start">{comp.name}</td>
                  
                  {/* get solves */}
                  {comp.solves.map((solve, sIdx) => (
                    <td className="text-end" key={sIdx}>{solve}</td>
                  ))}
                  
                  <td className="text-end">{comp.average}</td>
                  <td className="text-end">{comp.best}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
