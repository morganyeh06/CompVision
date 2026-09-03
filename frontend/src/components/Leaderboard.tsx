import './Leaderboard.css';
import { useState, useEffect } from 'react';
import EditBlack from '../assets/edit-black.svg';
import EditWhite from '../assets/edit-white.svg';
import AddBlack from '../assets/plus-black.svg';
import AddWhite from '../assets/plus-white.svg';
import DownloadBlack from '../assets/download-black.svg';
import DownloadWhite from '../assets/download-white.svg';

interface CompetitorResult {
    rank: number | string;
    name: string;
    solves: string[];
    best: string;
    average: string;
    is_finished: boolean;
}

interface EditState {
  name: string;
  solveIndex: number;
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

    // states for editing solves
    const [editingCell, setEditingCell] = useState<EditState | null>(null);
    const [editValue, setEditValue] = useState<string>("");

    const [appTheme, setAppTheme] = useState<string>(() => document.documentElement.getAttribute('data-bs-theme') || 'light');

    useEffect(() => {
      function handleThemeChange() {
        const current = document.documentElement.getAttribute('data-bs-theme') || 'light';
        setAppTheme(current);
      };

      window.addEventListener('themechange', handleThemeChange);
      return () => window.removeEventListener('themechange', handleThemeChange);
    }, []);

    const editIcon = appTheme === 'light' ? EditBlack : EditWhite;
    const addIcon = appTheme === 'light' ? AddBlack : AddWhite;
    const downloadIcon = appTheme === 'light' ? DownloadBlack : DownloadWhite;


    useEffect(() => {
      // fetchLeaderboard() returns the current leaderboard from the backend endpoint
      async function fetchLeaderboard() {
        try {
          const response = await fetch("http://127.0.0.1:8000/leaderboard", { cache: 'no-store' });
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
      const interval = setInterval(() => {
        // only fetch if not currently editing
        if (!editingCell) fetchLeaderboard();
      }, 1000);
      return () => clearInterval(interval);

    }, [editingCell]);

    // handleStartEdit(name, solveIndex, currentValue) sets the current cell
    // being edited and the value
    function handleStartEdit(name: string, solveIndex: number, currentValue: string) {
      setEditingCell({name, solveIndex})
      setEditValue(currentValue);
    }

    // handleSaveEdit() saves the edited cell and sends value to backend
    async function handleSaveEdit() {
      if(!editingCell) return;

      const payload = {
        competitor_name: editingCell?.name,
        solve_index: editingCell?.solveIndex,
        new_time: editValue.trim()
      };

      try {
        await fetch("http://127.0.0.1:8000/edit_result", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

      } catch(error) {
        console.error("Failed to edit result:", error);

      } finally {
        // stop editing the cell
        setEditingCell(null)
      }
    }

    // handleExportCSV() downloads the current leaderboard as a csv file
    function handleExportCSV() {
      window.open("http://127.0.0.1:8000/export_csv", "_blank");
    }


    return (
    <div className="leaderboard">
      <div className="leaderboard-top">
        <h5 className="leaderboard-title">{event} - Round {round}</h5>
        <div className="export" onClick={handleExportCSV} title="Export CSV">
          <h6 className="export-text">Export as CSV</h6>
          <img src={downloadIcon}></img>
        </div>
      </div>
      
      <div className="shadow-sm">
        <table className="table">
          <thead className="table text-muted">
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
                  {comp.solves.map((solve, sIdx) => {
                    const solveNum = sIdx + 1;
                    const isEditing = editingCell?.name === comp.name && editingCell?.solveIndex === solveNum;

                    return (
                      <td 
                        className="solve-cell text-end" 
                        key={sIdx}
                        onClick={() => !isEditing && handleStartEdit(comp.name, solveNum, solve)}
                      >
                        {isEditing ? (
                          <input
                            type="text"
                            className="form-control form-control-sm text-end"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            onBlur={handleSaveEdit}
                            onKeyDown={(e) => e.key === 'Enter' && handleSaveEdit()}
                            autoFocus
                          />
                        ) : (
                          <>
                            {solve}
                            {solve.trim() === "" ? (
                              <span className="add-icon">
                                <img src={addIcon}></img>
                              </span>
                            ) : (
                              <span className="edit-icon">
                                <img src={editIcon}></img>
                              </span>
                            )}
                            
                          </>
                        )}
                      </td>
                    );
                  })}
                  
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
