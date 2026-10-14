// Kitchen dashboard for The Royal Fork, fed by Supabase via FastAPI.
import { useEffect, useState } from 'react';
import OrderCard from '../../components/OrderCard.jsx';
import { getKitchenOrders, updateOrderStatus, sortByArrival } from '../../services/api.js';

// Sample board already in arrival order: oldest first, freshest last.
const FALLBACK_ORDERS = [
  {
    id: '103',
    table: 'T-07',
    status: 'completed',
    time: '12:20 PM',
    createdAt: '2026-10-10T12:20:00',
    items: [{ name: 'Veg Fried Rice', qty: 3, price: 520 }],
  },
  {
    id: '101',
    table: 'T-04',
    status: 'pending',
    time: '12:30 PM',
    createdAt: '2026-10-10T12:30:00',
    items: [
      { name: 'Chicken Biryani', qty: 2, price: 450 },
      { name: 'Garlic Naan', qty: 3, price: 120 },
      { name: 'Mango Lassi', qty: 2, price: 180 },
    ],
  },
  {
    id: '102',
    table: 'T-02',
    status: 'pending',
    time: '12:35 PM',
    createdAt: '2026-10-10T12:35:00',
    items: [
      { name: 'Margherita Pizza', qty: 1, price: 950 },
      { name: 'French Fries', qty: 2, price: 320 },
    ],
  },
];

const FILTERS = ['all', 'pending', 'completed', 'cancelled'];

export default function KitchenDashboard() {
  const [orders, setOrders] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [usingFallback, setUsingFallback] = useState(false);
  const today = new Date().toLocaleDateString('en-GB', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');
    getKitchenOrders()
      .then((rows) => {
        if (!active) return;
        if (rows.length === 0) {
          setOrders(sortByArrival(FALLBACK_ORDERS));
          setUsingFallback(true);
        } else {
          setOrders(sortByArrival(rows));
          setUsingFallback(false);
        }
      })
      .catch((err) => {
        if (!active) return;
        setError(`Backend unreachable (${err.message}). Showing sample data.`);
        setOrders(sortByArrival(FALLBACK_ORDERS));
        setUsingFallback(true);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const counts = {
    pending: orders.filter((o) => o.status === 'pending').length,
    completed: orders.filter((o) => o.status === 'completed').length,
    cancelled: orders.filter((o) => o.status === 'cancelled').length,
  };

  // First-come order first, freshest (last) order at the bottom of the board.
  const visible = sortByArrival(filter === 'all' ? orders : orders.filter((o) => o.status === filter));

  const changeStatus = async (id, status) => {
    // Optimistic update so the kitchen board feels instant.
    setOrders((prev) => sortByArrival(prev.map((o) => (o.id === id ? { ...o, status } : o))));
    if (usingFallback) return;
    try {
      const updated = await updateOrderStatus(id, status);
      setOrders((prev) => prev.map((o) => (o.id === updated.id ? updated : o)));
    } catch (err) {
      setError(`Could not save status: ${err.message}`);
    }
  };

  return (
    <main style={{ backgroundColor: '#f3f4f6', minHeight: '100vh', padding: '24px', fontFamily: 'Arial, sans-serif' }}>
      <header
        style={{
          backgroundColor: '#fff',
          borderRadius: '12px',
          padding: '20px 24px',
          marginBottom: '20px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '26px' }}>🍴 The Royal Fork — Kitchen Dashboard</h1>
            <p style={{ margin: '6px 0 0', color: '#6b7280' }}>📅 {today}</p>
            <p style={{ margin: '6px 0 0', fontSize: '13px', color: usingFallback ? '#92400e' : '#166534' }}>
              {loading ? 'Connecting to kitchen feed…' : usingFallback ? '⚠ Sample data — start backend for live orders' : '● Live from Supabase'}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <Stat label="Pending" value={counts.pending} color="#f59e0b" />
            <Stat label="Completed" value={counts.completed} color="#16a34a" />
            <Stat label="Cancelled" value={counts.cancelled} color="#dc2626" />
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', marginTop: '16px', flexWrap: 'wrap' }}>
          {FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: '7px 16px',
                borderRadius: '999px',
                border: filter === f ? '2px solid #111827' : '1px solid #d1d5db',
                backgroundColor: filter === f ? '#111827' : '#fff',
                color: filter === f ? '#fff' : '#374151',
                fontWeight: '700',
                fontSize: '13px',
                cursor: 'pointer',
                textTransform: 'capitalize',
              }}
            >
              {f} ({f === 'all' ? orders.length : counts[f]})
            </button>
          ))}
        </div>
      </header>

      <section
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: '16px',
        }}
      >
        {visible.map((order) => (
          <OrderCard key={order.id} order={order} onStatusChange={changeStatus} />
        ))}
      </section>

      {visible.length === 0 && (
        <p style={{ textAlign: 'center', color: '#6b7280', marginTop: '40px' }}>
          No {filter} orders right now.
        </p>
      )}
    </main>
  );
}

function Stat({ label, value, color }) {
  return (
    <div
      style={{
        backgroundColor: '#f9fafb',
        border: `1px solid ${color}`,
        borderRadius: '10px',
        padding: '8px 16px',
        textAlign: 'center',
        minWidth: '90px',
      }}
    >
      <div style={{ fontSize: '22px', fontWeight: '800', color }}>{value}</div>
      <div style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase' }}>{label}</div>
    </div>
  );
}
