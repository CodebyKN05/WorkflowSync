import { apiClient } from './client';

export const reconciliationApi = {
  triggerRun: (clientId) => 
    apiClient('/api/v1/reconciliation/run', {
      method: 'POST',
      body: JSON.stringify({ client_id: clientId })
    }),

  getRuns: (clientId) => 
    apiClient(`/api/v1/reconciliation/runs${clientId ? `?client_id=${clientId}` : ''}`),

  getRunSummary: (runId) => 
    apiClient(`/api/v1/reconciliation/runs/${runId}/summary`),

  getRunDetail: (runId) => 
    apiClient(`/api/v1/reconciliation/runs/${runId}/detail`),

  getQueue: (runId) => 
    apiClient(`/api/v1/reconciliation/runs/${runId}/queue`),

  confirmMatch: (matchId) => 
    apiClient(`/api/v1/reconciliation/matches/${matchId}/confirm`, {
      method: 'POST'
    }),

  rejectMatch: (matchId) => 
    apiClient(`/api/v1/reconciliation/matches/${matchId}/reject`, {
      method: 'POST'
    }),

  resolveInvoice: (invoiceId, transactionId) => 
    apiClient(`/api/v1/reconciliation/invoices/${invoiceId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ transaction_id: transactionId })
    }),
};
