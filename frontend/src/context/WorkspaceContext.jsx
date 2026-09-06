import { createContext, useState, useEffect, useContext } from 'react';
import { apiClient } from '../api/client';
import { useAuth } from './AuthContext';

const WorkspaceContext = createContext(null);

export function WorkspaceProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [firm, setFirm] = useState(null);
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClientState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadWorkspaceData() {
      if (!isAuthenticated) {
        setFirm(null);
        setClients([]);
        setSelectedClientState(null);
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const [firmData, clientsData] = await Promise.all([
          apiClient('/api/v1/firms/me'),
          apiClient('/api/v1/clients')
        ]);
        
        setFirm(firmData);
        setClients(clientsData);

        // Reconcile stored client
        const storedClientId = localStorage.getItem('selectedClientId');
        if (storedClientId) {
          const clientExists = clientsData.find(c => c.id === storedClientId);
          if (clientExists) {
            setSelectedClientState(clientExists);
          } else {
            localStorage.removeItem('selectedClientId');
            setSelectedClientState(null);
          }
        }
      } catch (err) {
        setError(err.data?.detail || 'Failed to load workspace data');
      } finally {
        setLoading(false);
      }
    }

    loadWorkspaceData();
  }, [isAuthenticated]);

  const setSelectedClient = (client) => {
    if (client) {
      localStorage.setItem('selectedClientId', client.id);
      setSelectedClientState(client);
    } else {
      localStorage.removeItem('selectedClientId');
      setSelectedClientState(null);
    }
  };

  const value = {
    firm,
    clients,
    selectedClient,
    setSelectedClient,
    loading,
    error
  };

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
}
