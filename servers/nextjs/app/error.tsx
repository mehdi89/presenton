'use client';

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    if (
      error.name === 'ChunkLoadError' ||
      error.message?.includes('Loading chunk') ||
      error.message?.includes('Failed to fetch dynamically imported module')
    ) {
      const reloaded = sessionStorage.getItem('chunk-reload');
      if (!reloaded) {
        sessionStorage.setItem('chunk-reload', '1');
        window.location.reload();
        return;
      }
      sessionStorage.removeItem('chunk-reload');
    }
  }, [error]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', gap: '16px' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Something went wrong</h2>
      <button
        onClick={() => {
          sessionStorage.removeItem('chunk-reload');
          window.location.reload();
        }}
        style={{ padding: '8px 16px', borderRadius: '6px', background: '#2563eb', color: '#fff', border: 'none', cursor: 'pointer' }}
      >
        Reload page
      </button>
    </div>
  );
}
