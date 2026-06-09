import "./globals.css";

// App-wide metadata (browser tab title, etc.).
export const metadata = {
  title: "Everything App — Module 0",
  description: "UI -> FastAPI -> LiteLLM gateway -> model",
};

// The root layout wraps every page. Minimal on purpose for Module 0.
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
