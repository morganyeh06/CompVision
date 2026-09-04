import './Banner.css';
import ThemeSwitch from './ThemeSwitch.tsx';
import GitHubLogo from '/src/assets/GitHub_Invertocat_Black.svg'

export default function Banner() {
    return (<>
        <div className="header">
            <p id="title">CompVision</p>
            <div className="tr-corner">
                <ThemeSwitch></ThemeSwitch>
                <div className="repo-link">
                    <a href="https://github.com/morganyeh06/CompVision" target='_blank'>
                        <img title='Project Repository' src={GitHubLogo} 
                            alt="Project Repository" className="link-img"></img>
                    </a>
                </div>
                
            </div>
        </div>
    </>);
};