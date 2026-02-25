import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["100", "200", "300", "400", "500", "600"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  weight: ["100", "300", "400"],
});

export const metadata: Metadata = {
  title: "+12 Monkeys",
  description: "Agent-as-a-Service platform with MCP integration",
  icons: {
    icon: "/favicon-monkey.png",
    apple: "/favicon-monkey.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} antialiased text-zinc-400 selection:bg-zinc-700 selection:text-white`}
        style={{ background: "#030303" }}
      >
        <div className="noise-overlay" />
        <div className="vignette" />
        {children}
      </body>
    </html>
  );
}
