// Shows whether a delivery robot is connected.
export default function RobotStatus({ online = false }) {
  return <p>Robot: {online ? 'online' : 'offline'}</p>;
}