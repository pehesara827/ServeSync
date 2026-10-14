// Labels a kitchen order status with a color-coded pill.
const styles = {
  pending: { backgroundColor: '#fef3c7', color: '#92400e', border: '1px solid #fbbf24' },
  completed: { backgroundColor: '#dcfce7', color: '#166534', border: '1px solid #22c55e' },
  cancelled: { backgroundColor: '#fee2e2', color: '#991b1b', border: '1px solid #ef4444' },
};

function normalize(status = 'unknown') {
  const value = String(status).toLowerCase().trim();
  if (value === 'complited' || value === 'complete' || value === 'completed' || value === 'done') return 'completed';
  if (value === 'cancel' || value === 'cancelled' || value === 'canceled') return 'cancelled';
  if (value === 'pending' || value === 'preparing' || value === 'new') return 'pending';
  return value;
}

const labels = { pending: 'Pending', completed: 'Completed', cancelled: 'Cancelled' };

export default function StatusBadge({ status = 'unknown' }) {
  const key = normalize(status);
  const style = styles[key] || { backgroundColor: '#e5e7eb', color: '#374151', border: '1px solid #9ca3af' };
  return (
    <span
      style={{
        ...style,
        display: 'inline-block',
        padding: '3px 12px',
        borderRadius: '999px',
        fontSize: '12px',
        fontWeight: '700',
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
      }}
    >
      {labels[key] || status}
    </span>
  );
}
