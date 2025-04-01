import { PublicClientApplication } from "@azure/msal-browser";

const msalConfig = {
  auth: {
    clientId: "4a2636df-2c24-4cbf-b55a-21eb0fae61b0",
    authority: "https://login.microsoftonline.com/4852d0fc-f87a-462b-ad09-773f986ccc04",
    redirectUri: "https://goalassist.ltdic.com/smarthr-form",
  },
};

const loginRequest = {
  scopes: [
    // "https://graph.microsoft.com/User.Read",
    "api://4a2636df-2c24-4cbf-b55a-21eb0fae61b0/FE_Auth"
  ],
};

const msalInstance = new PublicClientApplication(msalConfig);

export { msalInstance, loginRequest };
