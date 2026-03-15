import {
  createContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";

import type { AuthResponse, AuthUser, LoginPayload, RegisterPayload } from "@/types/auth";
import { fetchCurrentUser, loginRequest, registerRequest } from "@/services/api";

type AuthContextValue = {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<AuthResponse>;
  register: (payload: RegisterPayload) => Promise<AuthResponse>;
  logout: () => void;
  refreshCurrentUser: () => Promise<void>;
};

const AUTH_STORAGE_KEY = "aegiscore.auth";

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function persistAuth(authResponse: AuthResponse) {
  localStorage.setItem(
    AUTH_STORAGE_KEY,
    JSON.stringify({
      token: authResponse.access_token,
      user: authResponse.user,
    }),
  );
}

function readStoredAuth(): { token: string; user: AuthUser } | null {
  const storedValue = localStorage.getItem(AUTH_STORAGE_KEY);
  if (!storedValue) {
    return null;
  }

  try {
    return JSON.parse(storedValue) as { token: string; user: AuthUser };
  } catch {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedAuth = readStoredAuth();

    if (!storedAuth) {
      setIsLoading(false);
      return;
    }

    setToken(storedAuth.token);
    setUser(storedAuth.user);

    void fetchCurrentUser(storedAuth.token)
      .then((currentUser) => {
        setUser(currentUser);
        localStorage.setItem(
          AUTH_STORAGE_KEY,
          JSON.stringify({ token: storedAuth.token, user: currentUser }),
        );
      })
      .catch(() => {
        localStorage.removeItem(AUTH_STORAGE_KEY);
        setToken(null);
        setUser(null);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  const applyAuthResponse = (authResponse: AuthResponse) => {
    setToken(authResponse.access_token);
    setUser(authResponse.user);
    persistAuth(authResponse);
  };

  const login = async (payload: LoginPayload) => {
    const authResponse = await loginRequest(payload);
    applyAuthResponse(authResponse);
    return authResponse;
  };

  const register = async (payload: RegisterPayload) => {
    const authResponse = await registerRequest(payload);
    applyAuthResponse(authResponse);
    return authResponse;
  };

  const logout = () => {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    setToken(null);
    setUser(null);
  };

  const refreshCurrentUser = async () => {
    if (!token) {
      return;
    }

    const currentUser = await fetchCurrentUser(token);
    setUser(currentUser);
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token, user: currentUser }));
  };

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token && user),
      isLoading,
      login,
      register,
      logout,
      refreshCurrentUser,
    }),
    [user, token, isLoading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
