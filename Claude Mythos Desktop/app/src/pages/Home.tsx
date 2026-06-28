import Starfield from "@/components/effects/Starfield";
import Navigation from "@/components/Navigation";
import HeroSection from "@/sections/HeroSection";
import FeatureShowcase from "@/sections/FeatureShowcase";
import TerminalSection from "@/sections/TerminalSection";
import FooterSection from "@/sections/FooterSection";

export default function Home() {
  return (
    <>
      <Starfield />
      <Navigation />
      <div className="content-wrapper" style={{ position: "relative", zIndex: 10 }}>
        <HeroSection />
        <FeatureShowcase />
        <TerminalSection />
        <FooterSection />
      </div>
    </>
  );
}
