// Displays the current state of one restaurant table.
export default function TableCard({ table }) {
  return <article>Table {table?.id ?? 'unassigned'}</article>;
}