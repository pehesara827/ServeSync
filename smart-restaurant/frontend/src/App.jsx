// Shows the initial customer-facing screen.
import Navbar from './components/Navbar.jsx';
import KitchenDashboard from './pages/Kitchen/KitchenDashboard.jsx';

export default function App() {
  return (
    <>
      <Navbar />
      <KitchenDashboard />
    </>
  );
}
