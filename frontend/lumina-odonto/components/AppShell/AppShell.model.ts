import { matchesRoute } from "@/lib/auth/routes";

export function isNavItemActive(pathname: string, href: string): boolean {
  return matchesRoute(pathname, href);
}
