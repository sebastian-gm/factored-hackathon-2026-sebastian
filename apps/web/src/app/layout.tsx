import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aclara · LATAM Bank (demo)",
  description: "Synthetic data · Simulated bank · Not a real service",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
