import { PublicClientApplication } from "@azure/msal-browser";

const msalConfig = {
  auth: {
    clientId: "4a2636df-2c24-4cbf-b55a-21eb0fae61b0",
    authority: "https://login.microsoftonline.com/4852d0fc-f87a-462b-ad09-773f986ccc04",
    redirectUri: "http://4.240.80.139:3000/smarthr-form",
  },
};

const loginRequest = {
  scopes: ["User.Read"], 
};

const msalInstance = new PublicClientApplication(msalConfig);

export { msalInstance, loginRequest };
