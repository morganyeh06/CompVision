import './Dropdown.css';

interface Props {
    name: string
    id: string
    text: string
    options: Array<string>
}

export default function Dropdown( {name, id, text, options} : Props ) {
    // select options and CSS classes
    const dropdownOptions = options.map((opt) => (<option key={opt}>{opt}</option>));
    const classes = "form-select input-field"

    return (<>
        <div className='field-col'>
            <label className='input-label' htmlFor={id}>{text}</label>
            <select name={name} className={classes} id={id}>
                {dropdownOptions}
            </select>
        </div>
    </>);
};