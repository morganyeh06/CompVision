import './Dropdown.css';

interface Props {
    name: string
    id: string
    text: string
    options: Array<string>
    direction: string // one of {col, row}
    isDisabled: boolean
    setState: (s: string) => void
}

export default function Dropdown( {name, id, text, options, direction, isDisabled, setState} : Props ) {
    // select options and CSS classes
    const dropdownOptions = options.map((opt) => (<option key={opt}>{opt}</option>));
    const classes = "form-select input-field";
    const divClass = 'field-' + direction;
    const labelId = id + '-label';

    return (<>
        <div className={divClass}>
            <label className='input-label' id={labelId} htmlFor={id}>{text}</label>
            <select name={name} className={classes} id={id} onChange={(e) => setState(e.target.value)} disabled={isDisabled}>
                {dropdownOptions}
            </select>
        </div>
    </>);
};