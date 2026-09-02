import { useState, useEffect } from 'react';

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
    <div className="mt-4">
      <h3 className="mb-3">{event} - Round {round}</h3>
      
      <div className="table-responsive shadow-sm rounded">
        <table className="table table-bordered table-hover mb-0 text-center align-middle" style={{ backgroundColor: 'white' }}>
          <thead className="table-light text-muted">
            <tr>
              <th style={{ width: '50px' }}>#</th>
              <th className="text-start">Name</th>
              {/* create solve number columns */}
              {Array.from({ length: numSolves }, (_, i) => (
                <th key={i}>{i + 1}</th>
              ))}
              <th>{avgColName}</th>
              <th>Best</th>
            </tr>
          </thead>
          
          <tbody>
            {leaderboard.map((comp, idx) => {
              // green for finished, yellow for ongoing
              const rowStyle = comp.is_finished 
                ? { backgroundColor: '#00d65f', color: 'black', fontWeight: 'bold' } 
                : { backgroundColor: '#ffd500', color: 'black' };

              return (
                <tr key={idx}>
                  <td style={rowStyle}>{comp.rank}</td>
                  <td className="text-start fw-medium">{comp.name}</td>
                  
                  {/* get solves */}
                  {comp.solves.map((solve, sIdx) => (
                    <td key={sIdx}>{solve}</td>
                  ))}
                  
                  <td className="fw-bold">{comp.average}</td>
                  <td>{comp.best}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
