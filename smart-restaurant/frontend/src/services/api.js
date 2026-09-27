// Sends a JSON request to the Python backend.
export async function getOrders() {
  const response = await fetch('http://localhost:8000/api/orders');
  if (!response.ok) throw new Error('Could not load orders');
  return response.json();
}