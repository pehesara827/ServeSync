// Displays one kitchen order card with items, quantities and totals.
import StatusBadge from './StatusBadge.jsx';

export default function OrderCard({ order, onStatusChange }) {
  if (!order) return null;
  const total = order.items.reduce((sum, item) => sum + item.qty * item.price, 0);

  return (
    <article
      style={{
        backgroundColor: '#fff',
        borderRadius: '12px',
        border: '1px solid #e5e7eb',
        borderTop: `5px solid ${
          order.status === 'completed' ? '#22c55e' : order.status === 'cancelled' ? '#ef4444' : '#f59e0b'
        }`,
        padding: '16px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, fontSize: '18px' }}>Order #{order.id}</h3>
        <StatusBadge status={order.status} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px', color: '#4b5563' }}>
        <span>
          <strong>Table:</strong> {order.table}
        </span>
        <span>{order.time}</span>
      </div>

      <ul style={{ listStyle: 'none', margin: 0, padding: '10px 0', borderTop: '1px dashed #e5e7eb', borderBottom: '1px dashed #e5e7eb' }}>
        {order.items.map((item, index) => (
          <li
            key={index}
            style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: '14px' }}
          >
            <span>
              {item.name} <strong>x {item.qty}</strong>
              <span style={{ color: '#6b7280' }}> @ Rs. {item.price}</span>
            </span>
            <span style={{ fontWeight: '600' }}>Rs. {item.qty * item.price}</span>
          </li>
        ))}
      </ul>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '14px', color: '#6b7280' }}>
          {order.items.reduce((n, i) => n + i.qty, 0)} items
        </span>
        <span style={{ fontSize: '17px', fontWeight: '800' }}>Total: Rs. {total}</span>
      </div>

      <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
        {order.status === 'pending' && (
          <>
            <button
              onClick={() => onStatusChange(order.id, 'completed')}
              style={btnStyle('#16a34a')}
            >
              Mark Completed
            </button>
            <button
              onClick={() => onStatusChange(order.id, 'cancelled')}
              style={btnStyle('#dc2626')}
            >
              Cancel
            </button>
          </>
        )}
        {order.status !== 'pending' && (
          <button
            onClick={() => onStatusChange(order.id, 'pending')}
            style={btnStyle('#6b7280')}
          >
            Reset to Pending
          </button>
        )}
      </div>
    </article>
  );
}

function btnStyle(color) {
  return {
    flex: 1,
    backgroundColor: color,
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    padding: '8px 10px',
    fontSize: '13px',
    fontWeight: '700',
    cursor: 'pointer',
  };
}
