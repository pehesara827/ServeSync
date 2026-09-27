import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';

// Mounts the React application into the page.
createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>);