import './Panel.css';
import { useState } from 'react';
import Dropdown from './Dropdown.tsx';
import NumInput from './NumInput.tsx';

export interface CompSettings {
    competition_name: string;
    event: string;
    round_number: string;
    avg_format: string;
    competitors: string[];
}

interface Props {
    isRunning: boolean;
    isBackendReady: boolean;
    setIsRunning: (state: boolean) => void;
    saveSettings : (settings: CompSettings) => void;
}

export default function Panel( {isRunning, isBackendReady, setIsRunning, saveSettings} : Props ) {
    const eventOptions = ["3x3", "2x2", "4x4", "5x5", "6x6", "7x7", "3x3 OH", "3BLD",
                          "Pyraminx", "Megaminx", "Skewb", "Square-1", "Clock", "FTO"];
    const avgFormats = ["Ao5", "Mo3"];
    
    // competition settings
    const [compName, setCompName] = useState("");
    const [event, setEvent] = useState("3x3");
    const [round, setRound] = useState("1");
    const [format, setFormat] = useState("Ao5");
    const [competitors, setCompetitors] = useState("");
    
    // saved input values
    const [savedCompName, setSavedCompName] = useState("");
    const [savedEvent, setSavedEvent] = useState("3x3");
    const [savedRound, setSavedRound] = useState("1");
    const [savedFormat, setSavedFormat] = useState("Ao5");
    const [savedCompetitors, setSavedCompetitors] = useState("");

    // variables to determine whether Save button is enabled
    const isTextModified = compName != savedCompName || competitors != savedCompetitors;
    const isDropdownModified = event != savedEvent || format != savedFormat;
    const isNumInputModified = round != savedRound;
    const isValid = compName.trim() !== "" && competitors.trim() !== "";
    const isSaveEnabled = (isTextModified && isValid) || isDropdownModified || isNumInputModified ;

    
    // handleClick() changes app run state and saves settings
    function handleStart() {
        setIsRunning(true);
        handleSave();
    }

    async function handleStop() {
        if (!confirm("Are you sure you want to reset? All competition results will be lost.")) return;

        setIsRunning(false);
        try {
          fetch("http://127.0.0.1:8000/reset", { "method": "POST"})
        } catch(error) {
          console.error("Failed to reset backend state: ", error)
        }
    }

    // handleSave() sets the saved input values
    async function handleSave() {
        setSavedCompName(compName);
        setSavedEvent(event);
        setSavedRound(round);
        setSavedFormat(format);
        setSavedCompetitors(competitors);

        // parse competitors, split at newline
        const competitorList = competitors.split("\n").filter(name => name !== "");

        const payload: CompSettings = {
            competition_name: compName,
            event: event,
            round_number: round,
            avg_format: format,
            competitors: competitorList
        };

        try {
            // send payload to endpoint
            const response = await fetch("http://localhost:8000/settings", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });
            
            if (response.ok) {
                saveSettings(payload);
            } else {
                console.error("Server error when saving settings")
            }

        } catch (error) {
            console.error("Network error: ", error);
        }
    }

    return(<>
        <div className="panel shadow">
            <div className='config'>
                <div className='form-group text-start'>
                    <label className="input-label" htmlFor='comp-name'>Competition Name</label>
                    <input type="text" className='form-control' id="comp-name" onChange={(e) => setCompName(e.target.value)}></input>
                </div>
                <div className="config-row">
                    <Dropdown name="events" id="events" text="Event" options={eventOptions} direction='col' isDisabled={false} setState={setEvent}></Dropdown>
                    <NumInput id="round" minVal={1} defaultVal={1} text="Round" setState={setRound}></NumInput>
                    <Dropdown name='formats' id='formats' text='Format' options={avgFormats} direction='col' isDisabled={isRunning} setState={setFormat}></Dropdown>
                </div>
                <div className='form-group text-start'>
                    <label className="input-label" htmlFor='competitors'>Competitor List</label>
                    <textarea className="form-control" id='competitors' onChange={(e) => setCompetitors(e.target.value)}></textarea>
                </div>
            </div>
            <div className="btns">
                {!isRunning ? 
                    <button type="button" className="btn btn-primary" 
                            id='start-btn' onClick={handleStart} disabled={!isValid || !isBackendReady}>Start</button> : 
                    <>
                        <button type="button" className="btn btn-secondary" id='save-btn' disabled={!isSaveEnabled} onClick={handleSave}>Save</button>
                        <button type="button" className="btn btn-danger" id='stop-btn' onClick={handleStop}>Reset</button>
                    </>}
            </div>
            
        </div>
    </>);
};