import { NavLink, Outlet } from "react-router-dom";

function Layout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">R</div>
          <div>
            <h1>RetailLens</h1>
            <p>AWS Analytics</p>
          </div>
        </div>

        <nav className="nav-links">
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/products">
            Products
          </NavLink>
          <NavLink to="/refunds">
            Refunds
          </NavLink>
          <NavLink to="/pipeline">
            Pipeline
          </NavLink>
        </nav>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;