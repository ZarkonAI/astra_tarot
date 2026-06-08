import { AssetImage } from "./AssetImage";

interface StarGuideProps {
  size?: "hero" | "compact";
  variant?: "avatar" | "card" | "heroBanner" | "round";
}

const guideImages = {
  avatar: "assets/guide/guide_avatar.webp",
  card: "assets/guide/guide_card.webp",
  heroBanner: "assets/guide/hero_guide_banner.webp",
  round: "assets/logo/guide_round.webp",
};

export function StarGuide({ size = "compact", variant = "avatar" }: StarGuideProps) {
  return (
    <div className={`star-guide star-guide--${size} star-guide--${variant} guide-float`}>
      <AssetImage
        className="star-guide__image"
        path={guideImages[variant]}
        fallbackPath="assets/logo/guide_round.webp"
        alt="Звезда-проводник"
        fallback={
          <div className="star-guide__fallback" aria-label="Звезда-проводник">
            <span />
          </div>
        }
      />
    </div>
  );
}
