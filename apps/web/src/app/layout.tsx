import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aclara · LATAM Bank",
  description: "Banking support in Spanish and Portuguese",
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
