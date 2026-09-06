import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="text-center mt-20">
      <h2 className="text-2xl font-bold text-gray-900">404 - Not Found</h2>
      <p className="mt-2 text-gray-500">The page you are looking for does not exist.</p>
      <div className="mt-6">
        <Link to="/" className="text-blue-600 hover:text-blue-800">Go back home</Link>
      </div>
    </div>
  );
}
