import { NavLink, Outlet } from "react-router-dom";

const LINKS = [
  { to: "/", label: "Workspace", end: true },
  { to: "/history", label: "History", end: false },
];

export function AppLayout() {
  return (
    <div className="oi-shell">
      <header className="oi-topbar">
        <nav className="oi-topbar-inner" aria-label="Main navigation">
          <NavLink to="/" className="oi-brand" aria-label="OCR Intelligence home">
            OCR <em>Intelligence</em>
          </NavLink>
          <div className="oi-nav-links">
            {LINKS.map(({ to, label, end }) => (
              <NavLink key={to} to={to} end={end} className={({ isActive }) => `oi-nav-link${isActive ? " active" : ""}`}>
                {label}
              </NavLink>
            ))}
          </div>
          <span className="oi-topbar-note">Local MVP - no authentication</span>
        </nav>
      </header>
      <main className="oi-main">
        <Outlet />
      </main>
    </div>
  );
}
