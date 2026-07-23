import Keycloak from 'keycloak-js';

// Fallbacks ensure your app doesn't crash silently if an environment
// variable fails to inject during the SnapDeploy build process.
const keycloakConfig = {
  url: import.meta.env.VITE_KEYCLOAK_URL || "http://idp.vault.local:8080",
  realm: import.meta.env.VITE_KEYCLOAK_REALM || "secure-vault-realm",
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "vault-client"
};

// Sanitize: Strip trailing slashes to prevent double-slash (//) URL resolution errors
if (keycloakConfig.url.endsWith('/')) {
  keycloakConfig.url = keycloakConfig.url.slice(0, -1);
}

const keycloak = new Keycloak(keycloakConfig);

export default keycloak;
