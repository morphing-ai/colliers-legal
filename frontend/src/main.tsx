// frontend/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { ClerkProvider } from '@clerk/clerk-react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';

// Get Clerk publishable key from environment variable
const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string;

// Log environment info for debugging
console.log("Environment:", {
  MODE: import.meta.env.MODE,
  DEV: import.meta.env.DEV,
  PROD: import.meta.env.PROD,
  BASE_URL: import.meta.env.BASE_URL,
  CLERK_KEY_SET: !!clerkPubKey,
  CLERK_KEY_LENGTH: clerkPubKey?.length || 0,
  CLERK_KEY: clerkPubKey || 'NOT_SET'
});

if (!clerkPubKey) {
  console.error('Missing Clerk Publishable Key. Check environment variables.');
  // Show error in UI
  const root = document.getElementById('root');
  if (root) {
    root.innerHTML = `
      <div style="padding: 20px; margin: 20px; border: 2px solid red; background: #fee;">
        <h2>Configuration Error</h2>
        <p>Missing Clerk Publishable Key. The application cannot start without proper authentication configuration.</p>
        <p>Please contact the administrator.</p>
      </div>
    `;
  }
}

try {
  const rootElement = document.getElementById('root');
  
  if (!rootElement) {
    throw new Error("Failed to find #root element in the DOM. Check your index.html file.");
  }
  
  // Log Clerk initialization
  console.log("Initializing Clerk with key:", clerkPubKey ? `${clerkPubKey.substring(0, 20)}...` : "MISSING");
  
  // Check if we have a valid Clerk key
  if (!clerkPubKey) {
    console.error("No Clerk key provided, rendering error message");
    rootElement.innerHTML = `
      <div style="padding: 20px; text-align: center;">
        <h2>Configuration Error</h2>
        <p>Missing Clerk authentication key. Please check environment variables.</p>
      </div>
    `;
  } else {
    ReactDOM.createRoot(rootElement).render(
      <React.StrictMode>
        <ClerkProvider publishableKey={clerkPubKey}>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </ClerkProvider>
      </React.StrictMode>
    );
    
    console.log("React application successfully rendered!");
  }
} catch (error) {
  console.error("Failed to render React application:", error);
  
  // Create error display for debugging
  const errorDisplay = document.createElement('div');
  errorDisplay.style.padding = '20px';
  errorDisplay.style.margin = '20px';
  errorDisplay.style.border = '2px solid red';
  errorDisplay.style.borderRadius = '5px';
  errorDisplay.style.backgroundColor = '#ffeeee';
  
  errorDisplay.innerHTML = `
    <h1>React Application Failed to Start</h1>
    <p>There was an error initializing the React application:</p>
    <pre style="background: #f5f5f5; padding: 10px; overflow: auto;">${error instanceof Error ? error.stack || error.message : String(error)}</pre>
    <p>Check the browser console for more details.</p>
    
    <div style="margin-top: 20px; padding: 10px; background: #f0f0f0; border-radius: 5px;">
      <h3>Debugging Information:</h3>
      <ul>
        <li>Clerk Key Available: ${!!clerkPubKey}</li>
        <li>Clerk Key (first 5 chars): ${clerkPubKey ? clerkPubKey.substring(0, 5) + '...' : 'N/A'}</li>
        <li>Root Element Available: ${!!document.getElementById('root')}</li>
        <li>Browser: ${navigator.userAgent}</li>
      </ul>
    </div>
  `;
  
  document.body.appendChild(errorDisplay);
}