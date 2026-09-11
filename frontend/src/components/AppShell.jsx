import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useWorkspace } from '../context/WorkspaceContext';

export default function AppShell() {
  const { user, logout } = useAuth();
  const { firm, selectedClient, loading, error, setSelectedClient } = useWorkspace();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    setSelectedClient(null);
    logout();
  };

  const isClientSelectionPage = location.pathname === '/clients';

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <Link to="/" className="text-xl font-bold text-gray-900">WorkflowSync</Link>
                {firm && (
                  <span className="ml-4 text-sm font-medium text-gray-500 hidden sm:block border-l pl-4 border-gray-300">
                    {firm.name}
                  </span>
                )}
                {selectedClient && (
                  <div className="ml-4 flex items-center space-x-6 hidden sm:flex border-l pl-4 border-gray-300">
                    <span className="text-sm font-semibold text-blue-600">
                      {selectedClient.name}
                    </span>
                    <nav className="flex space-x-4">
                      <Link to="/" className={`text-sm font-medium ${location.pathname === '/' ? 'text-gray-900 border-b-2 border-gray-900' : 'text-gray-500 hover:text-gray-900'}`}>Dashboard</Link>
                      <Link to="/invoices" className={`text-sm font-medium ${location.pathname === '/invoices' ? 'text-gray-900 border-b-2 border-gray-900' : 'text-gray-500 hover:text-gray-900'}`}>Invoices</Link>
                      <Link to="/transactions" className={`text-sm font-medium ${location.pathname === '/transactions' ? 'text-gray-900 border-b-2 border-gray-900' : 'text-gray-500 hover:text-gray-900'}`}>Transactions</Link>
                      <Link to="/reconciliation" className={`text-sm font-medium ${location.pathname === '/reconciliation' ? 'text-gray-900 border-b-2 border-gray-900' : 'text-gray-500 hover:text-gray-900'}`}>Reconciliation</Link>
                    </nav>
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {selectedClient && !isClientSelectionPage && (
                <button
                  onClick={() => navigate('/clients')}
                  className="text-sm font-medium text-blue-600 hover:text-blue-800 transition"
                >
                  Switch Client
                </button>
              )}
              <span className="text-sm text-gray-500 hidden sm:block">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="text-sm font-medium text-gray-700 hover:text-gray-900 focus:outline-none focus:underline transition duration-150 ease-in-out"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
              {error}
            </div>
          )}
          {loading ? (
            <div className="flex justify-center py-12">
              <span className="text-gray-500">Loading workspace...</span>
            </div>
          ) : (
            <Outlet />
          )}
        </div>
      </main>
    </div>
  );
}
