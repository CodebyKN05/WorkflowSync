import { Navigate } from 'react-router-dom';
import { useWorkspace } from '../context/WorkspaceContext';

export default function Home() {
  const { selectedClient } = useWorkspace();

  if (!selectedClient) {
    return <Navigate to="/clients" replace />;
  }

  return (
    <div className="bg-white shadow sm:rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          Client Dashboard: {selectedClient.name}
        </h3>
        <div className="mt-2 max-w-xl text-sm text-gray-500">
          <p>
            You are currently viewing the workspace for <strong>{selectedClient.name}</strong>.
            Future increments will include the reconciliation dashboard, invoices, and transactions here.
          </p>
        </div>
      </div>
    </div>
  );
}
