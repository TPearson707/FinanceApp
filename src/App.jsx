import './app.scss';

import PrizeWinners from "./components/prizewinners/PrizeWinners";
import Navbar from './components/navbar/Navbar';

const App = () => {
  return (
    <div>
      <section className="Homepage">
        <Navbar/>
        <PrizeWinners/>
      </section>

      <section className="Banana"></section>
      </div>
  )
}

export default App
