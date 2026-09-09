import { useState, useEffect, useRef } from 'react';
import { Navigate } from 'react-router-dom';
import { useWorkspace } from '../context/WorkspaceContext';
import { apiClient } from '../api/client';

export default function Transactions() {
  const { selectedClient } = useWorkspace();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  
  const fileInputRef = useRef(null);

  const fetchTransactions = async () => {
    if (!selectedClient) return;
    
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient(`/api/v1/transactions?client_id=${selectedClient.id}`);
      setTransactions(data || []);
    } catch (err) {
      // Map known error codes based on the contract
      if (err.status === 404) {
        setError('Client not found.');
      } else if (err.status === 403) {
        setError("You are not authorized to access this client's transactions.");
      } else {
        setError(err.data?.detail || 'Failed to load transactions. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, [selectedClient]);

  const handleUpload = async (e) => {
    e.preventDefault();
    const file = fileInputRef.current?.files[0];
    
    if (!file) {
      setUploadError("Please select a CSV file to upload.");
      return;
    }

    if (!file.name.toLowerCase().endsWith('.csv') && file.type !== 'text/csv') {
      setUploadError("Only CSV files are allowed.");
      return;
    }

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    const formData = new FormData();
    formData.append('client_id', selectedClient.id);
    formData.append('file', file);

    try {
      const response = await apiClient('/api/v1/transactions/upload', {
        method: 'POST',
        body: formData
      });
      
      setUploadSuccess(response);
      fileInputRef.current.value = ''; // Reset file input
      await fetchTransactions(); // Refresh the list from the backend
    } catch (err) {
      // Translate known upload error codes
      if (err.status === 404) {
        setUploadError('Client not found.');
      } else if (err.status === 403) {
        setUploadError("You are not authorized to access this client.");
      } else if (err.status === 413) {
        setUploadError("The CSV file is too large.");
      } else if (err.status === 415) {
        setUploadError("Unsupported file format. Please upload a CSV file.");
      } else if (err.status === 422) {
        setUploadError("The CSV could not be processed. Please check its contents.");
      } else if (err.status === 500) {
        setUploadError("Transaction upload failed. Please try again.");
      } else {
        setUploadError(err.data?.detail || 'Failed to upload transactions.');
      }
    } finally {
      setUploading(false);
    }
  };

  if (!selectedClient) {
    return <Navigate to="/clients" replace />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow sm:rounded-lg px-4 py-5 sm:px-6">
        <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
          Transactions: {selectedClient.name}
        </h2>
      </div>

      {/* Upload Section */}
      <div className="bg-white shadow sm:rounded-lg px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Upload Transactions CSV</h3>
        
        {uploadError && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
            {uploadError}
          </div>
        )}

        {uploadSuccess && (
          <div className="mb-6 bg-green-50 border border-green-200 shadow-sm rounded-lg p-4">
            <h4 className="text-md font-bold text-green-800 mb-2">Upload Successful</h4>
            <p className="text-sm text-green-700 font-medium mb-1">
              {uploadSuccess.transactions_created} transactions created
            </p>
            {uploadSuccess.message && (
              <p className="text-sm text-green-600 mb-3">{uploadSuccess.message}</p>
            )}
            <div className="text-sm bg-white p-3 rounded border border-green-100">
               <div><strong>Filename:</strong> {uploadSuccess.filename}</div>
               <div><strong>Content Type:</strong> {uploadSuccess.content_type}</div>
            </div>
          </div>
        )}

        <form onSubmit={handleUpload} className="flex items-center space-x-4">
          <div className="flex-1 max-w-lg">
            <label htmlFor="csv-upload" className="sr-only">Choose CSV</label>
            <input
              id="csv-upload"
              name="file"
              type="file"
              accept=".csv,text/csv"
              ref={fileInputRef}
              disabled={uploading}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-md file:border-0
                file:text-sm file:font-medium
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100 disabled:opacity-50"
            />
          </div>
          <button
            type="submit"
            disabled={uploading}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {uploading ? 'Uploading...' : 'Upload CSV'}
          </button>
        </form>
      </div>

      {/* Ledger Section */}
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 border-b border-gray-200 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Transaction Ledger
          </h3>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="p-6 flex justify-center">
            <span className="text-gray-500 text-sm">Loading transactions...</span>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="p-6 flex flex-col items-center">
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={fetchTransactions}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              Retry
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && transactions.length === 0 && (
          <div className="px-4 py-12 text-center">
            <h3 className="mt-2 text-sm font-medium text-gray-900">No transactions yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              This client has no recorded transactions. Upload a CSV statement above to populate the ledger.
            </p>
          </div>
        )}

        {/* Table */}
        {!loading && !error && transactions.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Currency</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reference</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source File</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Uploaded At</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transactions.map((tx) => (
                  <tr key={tx.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {tx.transaction_date}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate" title={tx.description}>
                      {tx.description}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                      {Number(tx.amount).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {tx.currency}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {tx.reference || 'Not available'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {tx.source_file || 'Not available'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(tx.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
