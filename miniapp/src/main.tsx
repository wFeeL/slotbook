import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles/globals.css';

function App() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <h1 className="text-display text-rose">SlotBook ✦</h1>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
