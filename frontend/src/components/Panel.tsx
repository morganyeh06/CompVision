import './Panel.css';
import Dropdown from './Dropdown.tsx';
import NumInput from './NumInput.tsx';

export default function Panel() {
    const eventOptions = ["3x3", "2x2", "4x4", "5x5", "6x6", "7x7", "3x3 OH", "3BLD",
                          "Pyraminx", "Megaminx", "Skewb", "Square-1", "Clock", "FTO"];
    const avgFormats = ["Ao5", "Mo3"];

    return(<>
        <div className="panel">
            <div className='config'>
                <div className='input-group'>
                    <label className="input-label" htmlFor='comp-name'>Competition Name</label>
                    <input className='input-field' id="comp-name"></input>
                </div>
                <div className="config-row">
                    <Dropdown name="events" id="events" text="Event" options={eventOptions}></Dropdown>
                    <NumInput id="round" minVal={1} defaultVal={1} text="Round"></NumInput>
                    <Dropdown name='formats' id='formats' text='Format' options={avgFormats}></Dropdown>
                </div>
                <div className='input-group'>
                    <label className="input-label" htmlFor='competitors'>Competitor List</label>
                    <textarea id='competitors'></textarea>
                </div>
            </div>
            
        </div>
    </>);
};