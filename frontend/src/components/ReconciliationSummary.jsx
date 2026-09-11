import React from 'react';

export default function ReconciliationSummary({ summary }) {
  if (!summary) return null;

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
      <div className="px-4 py-5 sm:px-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">Run Summary</h3>
        <p className="mt-1 max-w-2xl text-sm text-gray-500">
          Status: {summary.status} | Started: {new Date(summary.started_at).toLocaleString()}
          {summary.completed_at && ` | Completed: ${new Date(summary.completed_at).toLocaleString()}`}
        </p>
      </div>
      <div className="border-t border-gray-200">
        <dl>
          <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-6">
            <dt className="text-sm font-medium text-gray-500 text-center">Matched</dt>
            <dt className="text-sm font-medium text-gray-500 text-center">Needs Review</dt>
            <dt className="text-sm font-medium text-gray-500 text-center">Duplicates</dt>
            <dt className="text-sm font-medium text-gray-500 text-center">Unmatched</dt>
          </div>
          <div className="bg-white px-4 py-2 sm:grid sm:grid-cols-4 sm:gap-4 sm:px-6 pb-5">
            <dd className="mt-1 text-3xl font-semibold text-green-600 text-center">{summary.matched_count}</dd>
            <dd className="mt-1 text-3xl font-semibold text-yellow-600 text-center">{summary.review_count}</dd>
            <dd className="mt-1 text-3xl font-semibold text-orange-600 text-center">{summary.duplicate_count}</dd>
            <dd className="mt-1 text-3xl font-semibold text-red-600 text-center">{summary.unmatched_count}</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
