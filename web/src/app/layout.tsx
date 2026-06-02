import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Luxury Vintage Bag Prices",
  description: "Track and compare luxury vintage handbag prices across marketplaces",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <a href="/" className="logo">
            Luxury Bag Prices
          </a>
          <nav>
            <a href="/">Search</a>
            <a href="/compare">Compare</a>
          </nav>
        </header>
        <main className="container">{children}</main>
      </body>
    </html>
  );
}
