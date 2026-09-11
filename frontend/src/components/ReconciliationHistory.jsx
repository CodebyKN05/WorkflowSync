import React from 'react';

export default function ReconciliationHistory({ runs, activeRunId, onSelectRun }) {
  if (!runs || runs.length === 0) {
    return (
      <div className="bg-white shadow sm:rounded-lg mb-6 p-12 text-center text-gray-500">
        Reconciliation history is empty. A reconciliation run must be performed before historical results are available.
      </div>
    );
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">COMPLETED</span>;
      case 'FAILED':
        return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">FAILED</span>;
      default:
        return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">{status}</span>;
    }
  };

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-lg">
      <div className="px-4 py-5 sm:px-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">Run History</h3>
      </div>
      <div className="border-t border-gray-200 overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Run ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Started</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Matched</th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Review</th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Duplicate</th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Unmatched</th>
              <th className="px-6 py-3"></th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {runs.map((run, idx) => {
              const isActive = run.id === activeRunId;
              const isLatest = idx === 0;

              return (
                <tr key={run.id} className={isActive ? 'bg-blue-50' : 'hover:bg-gray-50'}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-mono">
                    {run.id.substring(0, 8)}...
                    {isLatest && <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">Latest</span>}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(run.started_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(run.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 text-center font-semibold">{run.matched_count}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-yellow-600 text-center font-semibold">{run.review_count}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-orange-600 text-center font-semibold">{run.duplicate_count}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600 text-center font-semibold">{run.unmatched_count}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {isActive ? (
                      <span className="text-gray-400 font-semibold">Viewing</span>
                    ) : (
                      <button
                        onClick={() => onSelectRun(run)}
                        className="text-blue-600 hover:text-blue-900 font-semibold"
                      >
                        View
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
