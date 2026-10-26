/** Root pass-through — `<html>` / `<body>` live in `app/[locale]/layout.tsx`. */
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children
}
