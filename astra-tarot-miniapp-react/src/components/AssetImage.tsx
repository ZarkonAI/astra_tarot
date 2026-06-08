import { useEffect, useMemo, useState, type ImgHTMLAttributes, type ReactNode } from "react";
import { assetUrl } from "../services/assets";

interface AssetImageProps extends Omit<ImgHTMLAttributes<HTMLImageElement>, "src"> {
  path?: string;
  fallbackPath?: string;
  fallback?: ReactNode;
}

export function AssetImage({ path, fallbackPath, fallback, alt, ...imageProps }: AssetImageProps) {
  const sources = useMemo(() => [path, fallbackPath].filter((source): source is string => Boolean(source)), [path, fallbackPath]);
  const [sourceIndex, setSourceIndex] = useState(0);
  const currentSource = sources[sourceIndex];

  useEffect(() => {
    setSourceIndex(0);
  }, [path, fallbackPath]);

  if (!currentSource) {
    return <>{fallback}</>;
  }

  return (
    <img
      {...imageProps}
      src={assetUrl(currentSource)}
      alt={alt}
      onError={() => {
        setSourceIndex((index) => {
          const nextIndex = index + 1;
          return nextIndex < sources.length ? nextIndex : sources.length;
        });
      }}
    />
  );
}
