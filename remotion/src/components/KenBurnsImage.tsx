import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
} from "remotion";

interface Props {
  src: string;
  zoomStart?: number;
  zoomEnd?: number;
}

/**
 * 켄 번즈 효과 - 정지 이미지에 미세한 줌/패닝으로 생동감 부여.
 */
export const KenBurnsImage: React.FC<Props> = ({
  src,
  zoomStart = 1.0,
  zoomEnd = 1.12,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const scale = interpolate(frame, [0, durationInFrames], [zoomStart, zoomEnd], {
    extrapolateRight: "clamp",
  });

  // 약간의 패닝 효과
  const translateX = interpolate(frame, [0, durationInFrames], [0, -1.5], {
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(frame, [0, durationInFrames], [0, -1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill>
      <Img
        src={src}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translate(${translateX}%, ${translateY}%)`,
        }}
      />
    </AbsoluteFill>
  );
};
