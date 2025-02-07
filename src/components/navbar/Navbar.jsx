import { Link } from "react-router-dom"
import "./navbar.scss"

const Navbar = () => {
    return (
        <div className="navbar">
            <div className="wrapper">
                <ul>
                    <li><Link to="/">Home</Link></li>
                    <li><Link to="/dashboard">Dashboard</Link></li>
                    <li><Link to="/about">About</Link></li>
                    <li><Link to="/contact">Contact</Link></li>
                </ul>
            </div>
        </div>
    )
}

export default Navbar