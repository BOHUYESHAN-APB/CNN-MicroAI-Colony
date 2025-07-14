import { Outlet } from 'react-router-dom';
import '../index.css';

export default function Layout() {
  return (
    <div className="app-layout">
      <header className="app-header">
        <h1>Colony Analysis</h1>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
      <footer className="app-footer">
        <nav className="app-nav">
          <a href="/">Home</a>
          <a href="/analysis">Analysis</a>
          <a href="/history">History</a>
          <a href="/settings">Settings</a>
        </nav>
      </footer>
    </div>
  );
}
