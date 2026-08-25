import './Panel.css';
import { useState } from 'react';
import Dropdown from './Dropdown.tsx';
import NumInput from './NumInput.tsx';

interface Props {
    isRunning: boolean,
    setIsRunning: (state: boolean) => void
}

export default function Panel( {isRunning, setIsRunning} : Props ) {
    const eventOptions = ["3x3", "2x2", "4x4", "5x5", "6x6", "7x7", "3x3 OH", "3BLD",
                          "Pyraminx", "Megaminx", "Skewb", "Square-1", "Clock", "FTO"];
    const avgFormats = ["Ao5", "Mo3"];
    
    // current and saved text input values
    const [compName, setCompName] = useState("");
    const [competitors, setCompetitors] = useState("");
    const [savedCompName, setSavedCompName] = useState("");
    const [savedCompetitors, setSavedCompetitors] = useState("");

    // variables to determine whether Save button is enabled
    const isTextModified = compName != savedCompName || competitors != savedCompetitors;
    const isValid = compName.trim() !== "" && competitors.trim() !== "";
    const isSaveEnabled = isTextModified && isValid;

    
    // handleClick(action) changes app run state, may change saved input values
    // Parameters: 
    //      action (string): one of {start, stop}
    function handleClick(action: string) {
        setIsRunning(!isRunning);

        // on start set saved values to the current values
        if(action === "start") {
            setSavedCompName(compName);
            setSavedCompetitors(competitors);
        }
    }

    // handleSave() sets the saved input values
    function handleSave() {
        setSavedCompName(compName);
        setSavedCompetitors(competitors);
    }

    return(<>
        <div className="panel">
            <div className='config'>
                <div className='input-group'>
                    <label className="input-label" htmlFor='comp-name'>Competition Name</label>
                    <input className='input-field' id="comp-name" onChange={(e) => setCompName(e.target.value)}></input>
                </div>
                <div className="config-row">
                    <Dropdown name="events" id="events" text="Event" options={eventOptions} direction='col'></Dropdown>
                    <NumInput id="round" minVal={1} defaultVal={1} text="Round"></NumInput>
                    <Dropdown name='formats' id='formats' text='Format' options={avgFormats} direction='col'></Dropdown>
                </div>
                <div className='input-group'>
                    <label className="input-label" htmlFor='competitors'>Competitor List</label>
                    <textarea id='competitors' onChange={(e) => setCompetitors(e.target.value)}></textarea>
                </div>
            </div>
            <div className="btns">
                {!isRunning ? 
                    <button type="button" className="btn btn-primary" 
                            id='start-btn' onClick={() => {handleClick('start')}} disabled={!(competitors.trim() && compName.trim())}>Start</button> : 
                    <>
                        <button type="button" className="btn btn-secondary" id='save-btn' disabled={!isSaveEnabled} onClick={handleSave}>Save</button>
                        <button type="button" className="btn btn-danger" id='stop-btn' onClick={() => {handleClick('stop')}}>Stop</button>
                    </>}
            </div>
            
        </div>
    </>);
};