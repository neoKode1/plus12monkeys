import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Barlow_Condensed } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const barlowCondensed = Barlow_Condensed({
  variable: "--font-brand",
  subsets: ["latin"],
  weight: ["300", "400"],
});

export const metadata: Metadata = {
  title: "+12 Monkeys — Build AI Agents in Minutes",
  description: "Agent-as-a-Service platform with MCP integration",
  icons: {
    apple: "/favicon-monkey.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${barlowCondensed.variable} antialiased`}
        style={{ background: "#0D0D0D", color: "#E8E8E8" }}
      >
        {children}
      </body>
    </html>
  );
}
