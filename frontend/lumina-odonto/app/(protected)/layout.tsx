import ProtectedRoute from "@/components/Auth/ProtectedRoute";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return <ProtectedRoute>{children}</ProtectedRoute>;
}
