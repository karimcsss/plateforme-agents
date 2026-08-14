import './globals.css';

export const metadata = {
  title: 'Plateforme Multi-Agents',
  description: 'Orchestration dynamique d\'agents IA',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}