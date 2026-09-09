import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppShell from './components/AppShell';
import ProtectedRoute from './components/ProtectedRoute';
import Home from './pages/Home';
import Login from './pages/Login';
import ClientSelection from './pages/ClientSelection';
import NotFound from './pages/NotFound';
import Invoices from './pages/Invoices';
import Transactions from './pages/Transactions';
import { AuthProvider } from './context/AuthContext';
import { WorkspaceProvider } from './context/WorkspaceContext';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute><WorkspaceProvider><AppShell /></WorkspaceProvider></ProtectedRoute>}>
            <Route path="/" element={<Home />} />
            <Route path="/clients" element={<ClientSelection />} />
            <Route path="/invoices" element={<Invoices />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
