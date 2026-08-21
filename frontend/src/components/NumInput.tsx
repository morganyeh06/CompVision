import './NumInput.css'

interface Props {
    id: string;
    minVal: number;
    defaultVal: number;
    text: string;
}

export default function( {id, minVal, defaultVal, text} : Props ) {
    const classes = "form-control input-field";

    return (<>
        <div className="numinput-col">
            <label className="input-label" htmlFor={id}>{text}</label>
            <input type="number" className={classes}
                id={id} min={minVal} defaultValue={defaultVal}></input>
        </div>
    </>);
}