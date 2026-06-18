import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Email Generation Assistant",
  description: "Professional English email generation with Groq-backed evaluation."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

