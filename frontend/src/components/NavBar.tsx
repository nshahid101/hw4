import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";
import "./NavBar.css";

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <header className="navbar">
      <NavLink to="/" className="brand">
        Campus Customs
      </NavLink>
      <nav className="nav-links">
        <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
          Home
        </NavLink>
        <NavLink to="/products" className={({ isActive }) => (isActive ? "active" : "")}>
          Products
        </NavLink>
        <NavLink to="/about" className={({ isActive }) => (isActive ? "active" : "")}>
          About Us
        </NavLink>
        {user ? (
          <>
            <span className="nav-greeting">Hi, {user.first_name ?? user.name}</span>
            <button className="nav-cta" onClick={handleLogout}>
              Log Out
            </button>
          </>
        ) : (
          <>
            <NavLink to="/login" className={({ isActive }) => (isActive ? "active" : "")}>
              Log In
            </NavLink>
            <NavLink to="/create-account" className="nav-cta">
              Create Account
            </NavLink>
          </>
        )}
      </nav>
    </header>
  );
}
