import { api, tokenStorage, toApiError, type TokenPair } from "@/api/api";
import type { AuthUser, LoginCredentialsProps } from "./types";

export const authService = {
  // Erros sobem como ApiError (401 = credenciais inválidas, 429 = muitas tentativas, status null = rede).
  async login({
    username,
    password,
  }: LoginCredentialsProps): Promise<TokenPair> {
    const { data } = await api.post<TokenPair>(
      "/auth/login",
      new URLSearchParams({ username, password }),
      { headers: { "Content-Type": "application/x-www-form-urlencoded" } },
    );
    tokenStorage.setTokens(data);
    return data;
  },

  async getMe(): Promise<AuthUser> {
    const { data } = await api.get<AuthUser>("/auth/me");
    return data;
  },

  // Login completo: tokens + usuário. Se /auth/me falhar, não deixa tokens órfãos.
  async signIn(credentials: LoginCredentialsProps): Promise<AuthUser> {
    await authService.login(credentials);
    try {
      return await authService.getMe();
    } catch (error) {
      tokenStorage.clear();
      throw toApiError(error);
    }
  },

  // Recupera a sessão ao abrir o app (o interceptor renova o access token se preciso).
  // Sem token ou sessão inválida → null. Falha de rede mantém os tokens para tentar de novo.
  async restoreSession(): Promise<AuthUser | null> {
    if (!tokenStorage.getAccessToken()) return null;
    try {
      return await authService.getMe();
    } catch (error) {
      if (!toApiError(error).isNetworkError) tokenStorage.clear();
      return null;
    }
  },

  // Não há endpoint de logout: descartar tokens. A navegação fica com a UI.
  logout() {
    tokenStorage.clear();
  },
};
