import { useState, useEffect, useRef } from 'react';
import { Navigate } from 'react-router-dom';
import { useWorkspace } from '../context/WorkspaceContext';
import { apiClient } from '../api/client';

export default function Invoices() {
  const { selectedClient } = useWorkspace();
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  
  const fileInputRef = useRef(null);

  const fetchInvoices = async () => {
    if (!selectedClient) return;
    
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient(`/api/v1/invoices?client_id=${selectedClient.id}`);
      setInvoices(data || []);
    } catch (err) {
      setError(err.data?.detail || 'Failed to load invoices');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, [selectedClient]);

  const handleUpload = async (e) => {
    e.preventDefault();
    const file = fileInputRef.current?.files[0];
    
    if (!file) {
      setUploadError("Please select a PDF file to upload.");
      return;
    }

    if (file.type !== 'application/pdf') {
      setUploadError("Only PDF files are allowed.");
      return;
    }

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    const formData = new FormData();
    formData.append('client_id', selectedClient.id);
    formData.append('file', file);

    try {
      const response = await apiClient('/api/v1/invoices/upload', {
        method: 'POST',
        body: formData
      });
      
      setUploadSuccess(response);
      fileInputRef.current.value = ''; // Reset file input
      await fetchInvoices(); // Refresh the list
    } catch (err) {
      setUploadError(err.data?.detail || 'Failed to upload invoice');
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
          Invoices: {selectedClient.name}
        </h2>
      </div>

      {/* Upload Section */}
      <div className="bg-white shadow sm:rounded-lg px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Upload Invoice</h3>
        
        {uploadError && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
            {uploadError}
          </div>
        )}

        {uploadSuccess && (
          <div className="mb-6 bg-green-50 border border-green-200 shadow-sm rounded-lg p-4">
            <h4 className="text-md font-bold text-green-800 mb-2">Upload Successful</h4>
            <p className="text-sm text-green-700 mb-3">{uploadSuccess.message}</p>
            <div className="grid grid-cols-2 gap-4 text-sm bg-white p-3 rounded border border-green-100">
               <div><strong>Filename:</strong> {uploadSuccess.filename}</div>
               <div><strong>Vendor:</strong> {uploadSuccess.extracted_data?.vendor || 'Not available'}</div>
               <div><strong>Amount:</strong> {uploadSuccess.extracted_data?.total ? `${uploadSuccess.extracted_data.total} ${uploadSuccess.extracted_data.currency || ''}` : 'Not available'}</div>
               <div><strong>Invoice Date:</strong> {uploadSuccess.extracted_data?.invoice_date || 'Not available'}</div>
               <div><strong>Due Date:</strong> {uploadSuccess.extracted_data?.due_date || 'Not available'}</div>
               <div><strong>Invoice No:</strong> {uploadSuccess.extracted_data?.invoice_number || 'Not available'}</div>
            </div>
          </div>
        )}

        <form onSubmit={handleUpload} className="flex items-center space-x-4">
          <div className="flex-1 max-w-lg">
            <label htmlFor="file-upload" className="sr-only">Choose PDF</label>
            <input
              id="file-upload"
              name="file"
              type="file"
              accept=".pdf,application/pdf"
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
            {uploading ? 'Uploading...' : 'Upload PDF'}
          </button>
        </form>
      </div>

      {/* Ledger Section */}
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 border-b border-gray-200 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Invoice Ledger
          </h3>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="p-6 flex justify-center">
            <span className="text-gray-500 text-sm">Loading invoices...</span>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="p-6 flex flex-col items-center">
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={fetchInvoices}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              Retry
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && invoices.length === 0 && (
          <div className="px-4 py-12 text-center">
            <h3 className="mt-2 text-sm font-medium text-gray-900">No invoices found</h3>
            <p className="mt-1 text-sm text-gray-500">
              This client has no invoices yet. Upload a PDF invoice above to get started.
            </p>
          </div>
        )}

        {/* Table */}
        {!loading && !error && invoices.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vendor</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Invoice Date</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Uploaded At</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {invoices.map((inv) => (
                  <tr key={inv.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {inv.vendor || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {inv.amount ? `${Number(inv.amount).toFixed(2)} ${inv.currency || ''}` : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {inv.invoice_date || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        inv.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                        inv.status === 'matched' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {inv.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(inv.created_at).toLocaleString()}
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
