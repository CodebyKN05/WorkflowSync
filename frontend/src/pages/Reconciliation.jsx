import React, { useState, useEffect } from 'react';
import { useWorkspace } from '../context/WorkspaceContext';
import { reconciliationApi } from '../api/reconciliation';
import ReconciliationSummary from '../components/ReconciliationSummary';
import ReconciliationResults from '../components/ReconciliationResults';
import ReconciliationQueue from '../components/ReconciliationQueue';
import ReconciliationHistory from '../components/ReconciliationHistory';

export default function Reconciliation() {
  const { selectedClient } = useWorkspace();
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  
  const [latestRun, setLatestRun] = useState(null);
  const [allRuns, setAllRuns] = useState([]);
  const [summary, setSummary] = useState(null);
  const [results, setResults] = useState([]);
  const [queue, setQueue] = useState([]);
  
  const [activeTab, setActiveTab] = useState('QUEUE');

  // Fetch runs on mount or when selectedClient changes
  useEffect(() => {
    if (!selectedClient) {
      clearState();
      return;
    }
    fetchRuns(selectedClient.id);
  }, [selectedClient]);

  const clearState = () => {
    setLatestRun(null);
    setAllRuns([]);
    setSummary(null);
    setResults([]);
    setQueue([]);
    setError(null);
  };

  const fetchRuns = async (clientId) => {
    setLoading(true);
    setError(null);
    try {
      const runs = await reconciliationApi.getRuns(clientId);
      if (runs && runs.length > 0) {
        setAllRuns(runs);
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
      const [sumData, detData, queueData] = await Promise.all([
        reconciliationApi.getRunSummary(runId),
        reconciliationApi.getRunDetail(runId),
        reconciliationApi.getQueue(runId)
      ]);
      setSummary(sumData);
      setResults(detData);
      setQueue(queueData);
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
      setAllRuns(prev => [newRun, ...prev]);
      setLatestRun(newRun);
      setActiveTab('QUEUE');
      await fetchRunData(newRun.id);
    } catch (err) {
      console.error(err);
      setError('Failed to execute reconciliation run. Please try again.');
    } finally {
      setRunning(false);
    }
  };

  const handleSelectRun = async (run) => {
    setLatestRun(run);
    setActiveTab('QUEUE');
    await fetchRunData(run.id);
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
            onClick={() => fetchRuns(selectedClient.id)} 
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

          <div className="mb-4 border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('QUEUE')}
                className={`${
                  activeTab === 'QUEUE'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm`}
              >
                Review Queue
              </button>
              <button
                onClick={() => setActiveTab('RESULTS')}
                className={`${
                  activeTab === 'RESULTS'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm`}
              >
                Results Ledger
              </button>
              <button
                onClick={() => setActiveTab('HISTORY')}
                className={`${
                  activeTab === 'HISTORY'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm`}
              >
                Run History
              </button>
            </nav>
          </div>

          {activeTab === 'QUEUE' ? (
            <ReconciliationQueue 
              queue={queue} 
              onRefresh={fetchRunData} 
              runId={latestRun.id} 
            />
          ) : activeTab === 'RESULTS' ? (
            <ReconciliationResults results={results} />
          ) : (
            <ReconciliationHistory 
              runs={allRuns} 
              activeRunId={latestRun.id} 
              onSelectRun={handleSelectRun} 
            />
          )}
        </>
      )}
    </div>
  );
}
