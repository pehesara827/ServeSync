// Displays a brief summary of one order.
export default function OrderCard({ order }) {
  return <article>Order {order?.id ?? 'pending'}</article>;
}