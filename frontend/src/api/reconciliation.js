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
};
