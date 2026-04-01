import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

interface Props {
  type: "fade" | "slide" | "wipe" | "none";
  durationFrames: number;
  children: React.ReactNode;
}

/**
 * 장면 전환 효과 래퍼.
 * 장면 시작 시 페이드인/슬라이드인 적용.
 */
export const SceneTransition: React.FC<Props> = ({
  type,
  durationFrames,
  children,
}) => {
  const frame = useCurrentFrame();

  if (type === "none" || durationFrames === 0) {
    return <AbsoluteFill>{children}</AbsoluteFill>;
  }

  if (type === "fade") {
    const opacity = interpolate(frame, [0, durationFrames], [0, 1], {
      extrapolateRight: "clamp",
    });
    return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
  }

  if (type === "slide") {
    const translateX = interpolate(frame, [0, durationFrames], [100, 0], {
      extrapolateRight: "clamp",
    });
    return (
      <AbsoluteFill style={{ transform: `translateX(${translateX}%)` }}>
        {children}
      </AbsoluteFill>
    );
  }

  if (type === "wipe") {
    const progress = interpolate(frame, [0, durationFrames], [0, 100], {
      extrapolateRight: "clamp",
    });
    return (
      <AbsoluteFill
        style={{
          clipPath: `inset(0 ${100 - progress}% 0 0)`,
        }}
      >
        {children}
      </AbsoluteFill>
    );
  }

  return <AbsoluteFill>{children}</AbsoluteFill>;
};
