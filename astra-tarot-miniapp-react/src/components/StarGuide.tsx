import { useState } from "react";

interface StarGuideProps {
  size?: "hero" | "compact";
}

export function StarGuide({ size = "compact" }: StarGuideProps) {
  const [showImage, setShowImage] = useState(true);
  const imageSrc = `${import.meta.env.BASE_URL}assets/guide/guide_main.webp`;

  return (
    <div className={`star-guide star-guide--${size} guide-float`}>
      {showImage && (
        <img
          className="star-guide__image"
          src={imageSrc}
          alt="Звезда-проводник"
          onError={() => setShowImage(false)}
        />
      )}
      {!showImage && (
        <div className="star-guide__fallback" aria-label="Звезда-проводник">
          <span />
        </div>
      )}
    </div>
  );
}
