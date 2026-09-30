import type { Metadata } from "next";
import "./globals.css";
import "./insights.css";

export const metadata: Metadata = {
  title: "Aclara · Banco LATAM (demo)",
  description: "Synthetic data · Simulated bank · Not a real service",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
