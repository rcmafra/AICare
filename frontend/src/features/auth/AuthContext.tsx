import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import {
  ApiError,
  getStoredApiToken,
  loginWithApi,
  logoutFromApi,
  registerWithApi,
  setApiToken,
  validateApiSession,
} from '../../../api';

export type UserRole = 'Familiar' | 'Administrador';

export type AppUser = {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  familyId: string;
  inviteCode?: string;
};

export type RegisterData = {
  name: string;
  email: string;
  password: string;
  inviteCode?: string;
};

type AuthContextData = {
  user: AppUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<AppUser>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextData | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AppUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function restoreSession() {
      try {
        const token = await getStoredApiToken();
        if (!token) return;

        const session = await validateApiSession();
        if (active) setUser(session.user);
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          await setApiToken(null);
        } else {
          console.error('Não foi possível validar a sessão no backend:', error);
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void restoreSession();
    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail || !password) {
      throw new Error('Informe o e-mail e a senha.');
    }

    const session = await loginWithApi(normalizedEmail, password);
    await setApiToken(session.accessToken);
    setUser(session.user);
  }, []);

  const register = useCallback(async (data: RegisterData) => {
    const name = data.name.trim();
    const email = data.email.trim().toLowerCase();
    const inviteCode = data.inviteCode?.trim().toUpperCase();

    if (!name || !email || !data.password) {
      throw new Error('Preencha todos os campos obrigatórios.');
    }

    const session = await registerWithApi({
      name,
      email,
      password: data.password,
      inviteCode,
    });
    await setApiToken(session.accessToken);
    setUser(session.user);
    return session.user;
  }, []);

  const logout = useCallback(async () => {
    await logoutFromApi();
    await setApiToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser utilizado dentro de AuthProvider.');
  }
  return context;
}
