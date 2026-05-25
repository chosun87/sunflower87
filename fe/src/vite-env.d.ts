/// <reference types="vite/client" />

declare global {
  interface Window {
    gapi?: {
      load: (name: string, callback: () => void) => void;
      client?: {
        init: (options: Record<string, unknown>) => Promise<void>;
        setToken: (token: string | { access_token: string }) => void;
        getToken: () => { access_token: string } | null;
      };
    };
    google?: {
      accounts: {
        oauth2: {
          revoke: (token: string, callback: () => void) => void;
        };
      };
    };
  }
}

export {};
