import './ThemeSwitch.css'
import { useState, useEffect } from 'react';
import Sun from '/src/assets/sun.svg';
import Moon from '/src/assets/moon.svg';

export default function ThemeSwitch() {
    const [appTheme, setAppTheme] = useState(() => {
        // get saved theme from local storage, default to light
        const t = localStorage.getItem("theme");
        return t ? t : "light";
    });

    // handleChange() updates appTheme and saves to localStorage
    function handleThemeChange() {
        var theme = (appTheme === "light") ? "dark" : "light"

        setAppTheme(theme)
        localStorage.setItem("theme", theme)
    }

    // change them whenever appTheme is updated
    useEffect(() => {   
        // change App appearance depending on appTheme
        if (appTheme === "dark") {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
        }
    }, [appTheme]);


    return (<>
        <div className='theme-toggle'>
            <input type='checkbox' id='theme-switch' checked={appTheme === "dark"} onChange={handleThemeChange}></input>
            <label htmlFor='theme-switch'>
                <img src={appTheme === "dark" ? Moon : Sun} alt={appTheme === "dark" ? "moon" : "sun"} 
                    className="toggle-img" title="Toggle Light/Dark Mode"></img>
            </label>
        </div>
    </>)
};