import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import keycloak from './keycloak'

// Initialize Keycloak completely OUTSIDE of React
keycloak.init({
  onLoad: 'check-sso',
  checkLoginIframe: false,
  pkceMethod: 'S256'
}).then((authenticated) => {
  ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
      <App initialAuth={authenticated} />
    </React.StrictMode>,
  )
}).catch((error) => {
  console.error("Keycloak initialization failed:", error);
});
