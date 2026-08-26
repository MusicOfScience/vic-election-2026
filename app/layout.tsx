import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Victorian Election Forecast 2026",
  description:
    "A transparent dashboard for the Victorian state election forecasting model, historical validation, districts and regions.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en-AU">
      <body>{children}</body>
    </html>
  );
}
