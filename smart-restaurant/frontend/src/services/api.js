// Talks to the FastAPI backend, which proxies Supabase orders.
const API_BASE = 'http://localhost:8000';

async function request(path, options) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => '');
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

// Converts backend shape { table_number, created_at, item_name... }
// into dashboard card shape { table, time, name/qty... }.
export function mapOrder(row) {
  const created = row.created_at ? new Date(row.created_at) : null;
  return {
    id: String(row.id),
    table: `T-${String(row.table_number).padStart(2, '0')}`,
    status: row.status,
    time: created
      ? created.toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' })
      : '',
    date: created ? created.toLocaleDateString() : '',
    // Raw timestamp kept so the board can sort by arrival time.
    createdAt: created ? created.toISOString() : null,
    items: (row.items || []).map((item) => ({
      name: item.item_name ?? item.name,
      qty: item.quantity ?? item.qty,
      price: item.price,
    })),
  };
}

// Kitchen board order: first order that came in sits at the top, the
// freshest (last) order at the bottom. Orders without a timestamp fall
// back to their id so the list stays stable.
export function sortByArrival(rows) {
  const stamp = (row) => (row.createdAt ? Date.parse(row.createdAt) : null);
  const id = (row) => Number(row.id) || 0;
  return [...rows].sort((a, b) => {
    const left = stamp(a);
    const right = stamp(b);
    if (left !== null && right !== null && left !== right) return left - right;
    if (left === null && right !== null) return -1;
    if (left !== null && right === null) return 1;
    return id(a) - id(b);
  });
}

export async function getKitchenOrders(status) {
  const query = status && status !== 'all' ? `?status=${status}` : '';
  const rows = await request(`/api/kitchen/orders${query}`);
  return rows.map(mapOrder);
}

export async function getOrders(status) {
  const query = status && status !== 'all' ? `?status=${status}` : '';
  const rows = await request(`/api/orders${query}`);
  return rows.map(mapOrder);
}

export async function updateOrderStatus(id, status) {
  const row = await request(`/api/orders/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
  const order = mapOrder(row);
  // Backend now envelopes robot delivery; surface it without breaking cards.
  if (row && typeof row === 'object' && 'robot_dispatch' in row) {
    order.robotDispatch = row.robot_dispatch;
    if (
      row.robot_dispatch &&
      row.robot_dispatch.attempted &&
      !row.robot_dispatch.delivered
    ) {
      // Fail-open by design: order is saved, robot just didn't get told.
      console.warn(`Order ${id} saved but robot dispatch failed`, row.robot_dispatch);
    }
  }
  return order;
}
