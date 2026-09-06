import { Outlet, Link } from 'react-router-dom';

export default function AppShell() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <Link to="/" className="text-xl font-bold text-gray-900">WorkflowSync</Link>
              </div>
            </div>
            {/* Future auth/navigation controls can go here */}
            <div className="flex items-center">
              <span className="text-sm text-gray-500">Shell Mode</span>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
