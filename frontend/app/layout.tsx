import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import ClientProviders from "../components/ClientProviders";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "DietRiskNet - AI Meal Recognition & Disease Risk Dietary Assistant",
  description: "Vision-Language food recognition and personalized disease-risk-aware dietary recommendation using longitudinal meal analysis.",
  keywords: ["AI Dietitian", "Meal Recognition", "YOLOv8 Food", "Disease Risk Prediction", "Dietary Recommendation"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} h-full`}>
      <body className="min-h-full flex flex-col font-sans">
        <ClientProviders>
          {children}
        </ClientProviders>
      </body>
    </html>
  );
}
