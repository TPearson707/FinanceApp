import { Link } from "react-router-dom"
import "./navbar.scss"
import logo from "../../assets/logo.png";

const DbNavbar = () => {
    return (
        <div className="navbar">
            <div className="nav-left">
                <Link to="/"><img src={logo} alt="Logo" className="logo" /></Link>
            </div>
            <div className="nav-mid">
                <ul>
                    <li><Link to="/">Home</Link></li>
                    <li><Link to="/dashboard">Applied</Link></li>
                    <li><Link to="/about">Saved</Link></li>
                </ul>
            </div>
            <div className="nav-right">
                <Link to="/contact">About</Link>
                <Link to="/">Profile</Link>
            </div>

        </div>
    )
}

export default DbNavbar