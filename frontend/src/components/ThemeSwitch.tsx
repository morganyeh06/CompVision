import './ThemeSwitch.css'
import { useState, useEffect } from 'react';
import Sun from '/src/assets/sun.svg';
import Moon from '/src/assets/moon.svg';

export default function ThemeSwitch() {
    const [appTheme, setAppTheme] = useState(() => {
        // get saved theme from local storage, default to browser preference
        const t = localStorage.getItem("theme");
        if (t) return t;

        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    });

    // toggleTheme() updates appTheme and saves to localStorage
    function toggleTheme() {
        setAppTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
    }

    // change them whenever appTheme is updated
    useEffect(() => {   
        // change App appearance depending on appTheme
        document.documentElement.setAttribute('data-bs-theme', appTheme);
        localStorage.setItem('theme', appTheme)

        // trigger theme change event
        window.dispatchEvent(new Event('themechange'));
    }, [appTheme]);


    return (<>
        <div className='theme-toggle'>
            <input type='checkbox' id='theme-switch' checked={appTheme === "dark"} onChange={toggleTheme}></input>
            <label htmlFor='theme-switch'>
                <img src={appTheme === "dark" ? Moon : Sun} alt={appTheme === "dark" ? "moon" : "sun"} 
                    className="toggle-img" title="Toggle Light/Dark Mode"></img>
            </label>
        </div>
    </>)
};