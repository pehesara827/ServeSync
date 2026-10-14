// Provides the shared application navigation.
export default function Navbar() {
  return (
    <nav
      aria-label="Main navigation"
      style={{
        backgroundColor: '#111827',
        color: '#fff',
        padding: '12px 24px',
        fontSize: '18px',
        fontWeight: '800',
        letterSpacing: '0.5px',
      }}
    >
      🍴 The Royal Fork <span style={{ fontWeight: '400', fontSize: '14px', opacity: 0.8 }}>— Smart Restaurant</span>
    </nav>
  );
}
