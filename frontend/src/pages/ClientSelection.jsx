import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWorkspace } from '../context/WorkspaceContext';

export default function ClientSelection() {
  const { clients, selectedClient, setSelectedClient, firm } = useWorkspace();
  const navigate = useNavigate();

  // If a client is already selected and we mount this component,
  // we might want to stay here so the user can switch.
  
  const handleSelectClient = (client) => {
    setSelectedClient(client);
    navigate('/');
  };

  if (!clients || clients.length === 0) {
    return (
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6 text-center">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            No Clients Available
          </h3>
          <div className="mt-2 max-w-xl text-sm text-gray-500 mx-auto">
            <p>
              Your firm ({firm?.name}) currently has no clients associated with it.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow sm:rounded-lg">
      <div className="px-4 py-5 sm:border-b sm:border-gray-200 sm:px-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          Select a Client
        </h3>
        <p className="mt-1 text-sm text-gray-500">
          Choose a client to proceed with reconciliation or view history.
        </p>
      </div>
      <ul className="divide-y divide-gray-200">
        {clients.map((client) => (
          <li key={client.id}>
            <button
              onClick={() => handleSelectClient(client)}
              className={`w-full text-left px-4 py-4 sm:px-6 hover:bg-gray-50 focus:outline-none focus:bg-gray-50 transition duration-150 ease-in-out ${
                selectedClient?.id === client.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
              }`}
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-blue-600 truncate">
                  {client.name}
                </p>
                <div className="ml-2 flex-shrink-0 flex">
                  <p className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    {client.currency}
                  </p>
                </div>
              </div>
              <div className="mt-2 sm:flex sm:justify-between">
                <div className="sm:flex">
                  <p className="flex items-center text-sm text-gray-500">
                    {client.industry || 'No industry specified'}
                  </p>
                </div>
              </div>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
