import { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useWorkspace } from '../context/WorkspaceContext';
import { apiClient } from '../api/client';

export default function Home() {
  const { selectedClient } = useWorkspace();
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchRuns = async () => {
    if (!selectedClient) return;
    
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient(`/api/v1/reconciliation/runs?client_id=${selectedClient.id}`);
      setRuns(data || []);
    } catch (err) {
      setError(err.data?.detail || 'Failed to load reconciliation history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, [selectedClient]);

  if (!selectedClient) {
    return <Navigate to="/clients" replace />;
  }

  const latestRun = runs.length > 0 ? runs[0] : null;

  return (
    <div className="space-y-6">
      {/* Dashboard Header */}
      <div className="bg-white shadow sm:rounded-lg px-4 py-5 sm:px-6">
        <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
          Dashboard: {selectedClient.name}
        </h2>
        <div className="mt-1 flex flex-col sm:flex-row sm:flex-wrap sm:mt-0 sm:space-x-6">
          <div className="mt-2 flex items-center text-sm text-gray-500">
            {selectedClient.industry ? `Industry: ${selectedClient.industry}` : 'No industry specified'}
          </div>
          <div className="mt-2 flex items-center text-sm text-gray-500">
            Currency: {selectedClient.currency}
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="bg-white shadow sm:rounded-lg p-6 flex justify-center">
          <span className="text-gray-500 text-sm">Loading dashboard data...</span>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="bg-red-50 border border-red-200 shadow sm:rounded-lg p-6 flex flex-col items-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchRuns}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && !latestRun && (
        <div className="bg-white shadow sm:rounded-lg px-4 py-12 text-center">
          <h3 className="mt-2 text-sm font-medium text-gray-900">No reconciliation runs yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Reconciliation results will appear here after a run has been completed.
          </p>
        </div>
      )}

      {/* Latest Run Data */}
      {!loading && !error && latestRun && (
        <div className="space-y-6">
          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 border-b border-gray-200 sm:px-6 flex justify-between items-center">
              <div>
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Latest Reconciliation
                </h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  Started: {new Date(latestRun.started_at).toLocaleString()}
                </p>
              </div>
              <span className={`inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium ${
                latestRun.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                latestRun.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {latestRun.status}
              </span>
            </div>
            <div className="px-4 py-5 sm:p-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
              
              <div className="bg-white overflow-hidden shadow rounded-lg border border-gray-100">
                <div className="px-4 py-5 sm:p-6">
                  <dt className="text-sm font-medium text-gray-500 truncate">Matched</dt>
                  <dd className="mt-1 text-3xl font-semibold text-gray-900">{latestRun.matched_count}</dd>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg border border-gray-100">
                <div className="px-4 py-5 sm:p-6">
                  <dt className="text-sm font-medium text-yellow-600 truncate">Needs Review</dt>
                  <dd className="mt-1 text-3xl font-semibold text-gray-900">{latestRun.review_count}</dd>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg border border-gray-100">
                <div className="px-4 py-5 sm:p-6">
                  <dt className="text-sm font-medium text-red-600 truncate">Unmatched</dt>
                  <dd className="mt-1 text-3xl font-semibold text-gray-900">{latestRun.unmatched_count}</dd>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg border border-gray-100">
                <div className="px-4 py-5 sm:p-6">
                  <dt className="text-sm font-medium text-gray-500 truncate">Possible Duplicates</dt>
                  <dd className="mt-1 text-3xl font-semibold text-gray-900">{latestRun.duplicate_count}</dd>
                </div>
              </div>

            </div>
          </div>
        </div>
      )}
    </div>
  );
}
