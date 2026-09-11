import React, { useState } from 'react';
import { reconciliationApi } from '../api/reconciliation';

export default function ReconciliationQueue({ queue, onRefresh, runId }) {
  const [processingId, setProcessingId] = useState(null);
  const [error, setError] = useState(null);

  if (!queue || queue.length === 0) {
    return (
      <div className="bg-white shadow sm:rounded-lg mb-6 p-12 text-center text-gray-500">
        No items require review.
      </div>
    );
  }

  // Group candidates by invoice.id
  const grouped = queue.reduce((acc, candidate) => {
    const invId = candidate.invoice.id;
    if (!acc[invId]) {
      acc[invId] = {
        invoice: candidate.invoice,
        candidates: []
      };
    }
    acc[invId].candidates.push(candidate);
    return acc;
  }, {});

  const groups = Object.values(grouped);

  const handleAction = async (actionType, candidate) => {
    setProcessingId(candidate.id);
    setError(null);
    try {
      if (actionType === 'CONFIRM') {
        await reconciliationApi.confirmMatch(candidate.id);
      } else if (actionType === 'REJECT') {
        await reconciliationApi.rejectMatch(candidate.id);
      } else if (actionType === 'RESOLVE') {
        await reconciliationApi.resolveInvoice(candidate.invoice.id, candidate.transaction.id);
      }
      if (onRefresh) await onRefresh(runId);
    } catch (err) {
      console.error(err);
      setError(`Failed to ${actionType.toLowerCase()} candidate. Please refresh and try again.`);
    } finally {
      setProcessingId(null);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'NEEDS_REVIEW':
        return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">NEEDS REVIEW</span>;
      case 'DUPLICATE':
        return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-orange-100 text-orange-800">DUPLICATE</span>;
      default:
        return <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">{status}</span>;
    }
  };

  return (
    <div className="space-y-6 mb-6">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm flex justify-between items-center">
          <span>{error}</span>
          <button 
            onClick={() => { setError(null); if (onRefresh) onRefresh(runId); }}
            className="text-red-700 underline font-medium hover:text-red-900"
          >
            Refresh
          </button>
        </div>
      )}

      {groups.map((group) => {
        const { invoice, candidates } = group;
        const isDuplicate = candidates.length > 1;

        return (
          <div key={invoice.id} className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="bg-gray-50 px-4 py-4 sm:px-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Invoice: {invoice.invoice_number}
                  </h3>
                  <p className="mt-1 max-w-2xl text-sm text-gray-500">
                    {invoice.vendor} • {invoice.invoice_date} • {parseFloat(invoice.amount).toFixed(2)} {invoice.currency}
                  </p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500">Candidates: {candidates.length}</span>
                </div>
              </div>
            </div>

            <ul className="divide-y divide-gray-200">
              {candidates.map((candidate) => {
                const tx = candidate.transaction;
                const isProcessing = processingId === candidate.id;
                const isAnyProcessing = processingId !== null;

                return (
                  <li key={candidate.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex-1 pr-4">
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-sm font-medium text-blue-600 truncate">
                            {tx.description}
                          </p>
                          <div className="ml-2 flex-shrink-0 flex">
                            {getStatusBadge(candidate.status)}
                          </div>
                        </div>
                        <div className="mt-2 sm:flex sm:justify-between">
                          <div className="sm:flex">
                            <p className="flex items-center text-sm text-gray-500">
                              {tx.transaction_date} • {parseFloat(tx.amount).toFixed(2)} {tx.currency}
                              {tx.reference && ` • Ref: ${tx.reference}`}
                            </p>
                          </div>
                          <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                            Score: {parseFloat(candidate.score).toFixed(1)}
                          </div>
                        </div>
                        <div className="mt-2 text-xs text-gray-500 whitespace-pre-line">
                          {candidate.reason}
                        </div>
                      </div>

                      <div className="flex-shrink-0 flex space-x-2 border-l border-gray-200 pl-4 ml-2">
                        {isDuplicate ? (
                          <button
                            onClick={() => handleAction('RESOLVE', candidate)}
                            disabled={isAnyProcessing}
                            className={`inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded shadow-sm text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
                              ${isAnyProcessing ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}`}
                          >
                            {isProcessing ? 'Resolving...' : 'Resolve'}
                          </button>
                        ) : (
                          <>
                            <button
                              onClick={() => handleAction('CONFIRM', candidate)}
                              disabled={isAnyProcessing}
                              className={`inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded shadow-sm text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500
                                ${isAnyProcessing ? 'bg-green-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700'}`}
                            >
                              {isProcessing ? '...' : 'Confirm'}
                            </button>
                            <button
                              onClick={() => handleAction('REJECT', candidate)}
                              disabled={isAnyProcessing}
                              className={`inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded shadow-sm text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500
                                ${isAnyProcessing ? 'bg-red-400 cursor-not-allowed' : 'bg-red-600 hover:bg-red-700'}`}
                            >
                              {isProcessing ? '...' : 'Reject'}
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        );
      })}
    </div>
  );
}
