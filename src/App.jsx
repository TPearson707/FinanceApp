import './app.scss';

import Navbar from "./components/dashboard/navbar/Navbar"
import Dashboard from './components/dashboard/Dashboard';

const App = () => {
  return (
    <div>
      <section className="Homepage">
        <Navbar/>
        <Dashboard/>
      </section>

      <section className="banana">Banana</section>

      </div>
  )
}

export default App
