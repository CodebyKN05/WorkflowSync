import React, { useState, useEffect } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { reconciliationApi } from '../api/reconciliation';
import ReconciliationSummary from '../components/ReconciliationSummary';
import ReconciliationResults from '../components/ReconciliationResults';

export default function Reconciliation() {
  const { selectedClient } = useWorkspace();
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  
  const [latestRun, setLatestRun] = useState(null);
  const [summary, setSummary] = useState(null);
  const [results, setResults] = useState([]);

  // Fetch runs on mount or when selectedClient changes
  useEffect(() => {
    if (!selectedClient) {
      clearState();
      return;
    }
    fetchLatestRun(selectedClient.id);
  }, [selectedClient]);

  const clearState = () => {
    setLatestRun(null);
    setSummary(null);
    setResults([]);
    setError(null);
  };

  const fetchLatestRun = async (clientId) => {
    setLoading(true);
    setError(null);
    try {
      const runs = await reconciliationApi.getRuns(clientId);
      if (runs && runs.length > 0) {
        const firstRun = runs[0]; // Newest first
        setLatestRun(firstRun);
        await fetchRunData(firstRun.id);
      } else {
        clearState();
      }
    } catch (err) {
      console.error(err);
      setError('Failed to fetch reconciliation history.');
      clearState();
    } finally {
      setLoading(false);
    }
  };

  const fetchRunData = async (runId) => {
    try {
      const [sumData, detData] = await Promise.all([
        reconciliationApi.getRunSummary(runId),
        reconciliationApi.getRunDetail(runId)
      ]);
      setSummary(sumData);
      setResults(detData);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch details for the latest run.');
    }
  };

  const handleRunReconciliation = async () => {
    if (!selectedClient) return;
    setRunning(true);
    setError(null);
    try {
      const newRun = await reconciliationApi.triggerRun(selectedClient.id);
      setLatestRun(newRun);
      await fetchRunData(newRun.id);
    } catch (err) {
      console.error(err);
      setError('Failed to execute reconciliation run. Please try again.');
    } finally {
      setRunning(false);
    }
  };

  if (!selectedClient) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-medium text-gray-900">Select a client to view reconciliation</h2>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Reconciliation: {selectedClient.name}
        </h1>
        <button
          onClick={handleRunReconciliation}
          disabled={running || loading}
          className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
            ${running || loading ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}
        >
          {running ? 'Running...' : 'Run Reconciliation'}
        </button>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm flex justify-between items-center">
          <span>{error}</span>
          <button 
            onClick={() => fetchLatestRun(selectedClient.id)} 
            className="text-red-700 underline font-medium hover:text-red-900"
          >
            Retry
          </button>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading reconciliation data...</div>
      ) : !latestRun ? (
        <div className="bg-white shadow sm:rounded-lg mb-6 p-12 text-center">
          <p className="text-gray-500 mb-4">Reconciliation has not been run for this client yet.</p>
        </div>
      ) : (
        <>
          <ReconciliationSummary summary={summary} />
          <ReconciliationResults results={results} />
        </>
      )}
    </div>
  );
}
