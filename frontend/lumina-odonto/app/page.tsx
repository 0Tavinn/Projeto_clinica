import type { Metadata } from "next";
import GuestRoute from "@/components/Auth/GuestRoute";
import Login from "@/components/Login/Login";

export const metadata: Metadata = { title: "Entrar" };

export default function LoginPage() {
  return (
    <GuestRoute>
      <Login />
    </GuestRoute>
  );
}
