// Labels a status with a compact text element.
export default function StatusBadge({ status = 'unknown' }) {
  return <span>{status}</span>;
}