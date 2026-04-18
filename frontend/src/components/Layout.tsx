import { Link, Outlet, useLocation } from "react-router-dom";

const NAV = [
  { to: "/people", label: "People" },
  { to: "/imports", label: "Import" },
];

export default function Layout() {
  const { pathname } = useLocation();
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-6">
        <span className="font-bold text-lg text-indigo-600">Lynk</span>
        {NAV.map(({ to, label }) => (
          <Link
            key={to}
            to={to}
            className={`text-sm font-medium ${
              pathname.startsWith(to)
                ? "text-indigo-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {label}
          </Link>
        ))}
        <Link
          to="/people/new"
          className="ml-auto text-sm font-medium bg-indigo-600 text-white px-3 py-1.5 rounded hover:bg-indigo-700"
        >
          + Add person
        </Link>
      </nav>
      <main className="max-w-7xl mx-auto px-6 py-6">
        <Outlet />
      </main>
    </div>
  );
}
