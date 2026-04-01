import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface Props {
  text: string;
  fontSize?: number;
  fontFamily?: string;
  color?: string;
  backgroundColor?: string;
  position?: "bottom" | "center" | "top";
}

/**
 * 자막 컴포넌트 - 페이드인 + 하단/중앙/상단 배치.
 */
export const Subtitle: React.FC<Props> = ({
  text,
  fontSize = 48,
  fontFamily = "Malgun Gothic, sans-serif",
  color = "#FFFFFF",
  backgroundColor = "rgba(0,0,0,0.6)",
  position = "bottom",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // 페이드인 (처음 10프레임)
  const fadeIn = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 페이드아웃 (마지막 10프레임)
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 10, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp" }
  );

  const opacity = Math.min(fadeIn, fadeOut);

  const positionStyle: React.CSSProperties = {
    top: position === "top" ? 60 : undefined,
    bottom: position === "bottom" ? 60 : undefined,
    top: position === "center" ? "50%" : undefined,
    transform: position === "center" ? "translateY(-50%)" : undefined,
  };

  // 긴 텍스트는 여러 줄로 분할
  const maxCharsPerLine = 25;
  const lines: string[] = [];
  let remaining = text;
  while (remaining.length > maxCharsPerLine) {
    let breakPoint = remaining.lastIndexOf(" ", maxCharsPerLine);
    if (breakPoint === -1) breakPoint = maxCharsPerLine;
    lines.push(remaining.slice(0, breakPoint));
    remaining = remaining.slice(breakPoint).trim();
  }
  if (remaining) lines.push(remaining);

  return (
    <AbsoluteFill
      style={{
        justifyContent: position === "center" ? "center" : undefined,
        alignItems: "center",
        ...positionStyle,
        position: "absolute",
        opacity,
      }}
    >
      <div
        style={{
          position: "absolute",
          bottom: position === "bottom" ? 60 : undefined,
          top: position === "top" ? 60 : undefined,
          padding: "12px 28px",
          borderRadius: 8,
          backgroundColor,
          maxWidth: "85%",
          textAlign: "center",
        }}
      >
        {lines.map((line, i) => (
          <div
            key={i}
            style={{
              fontSize,
              fontFamily,
              color,
              fontWeight: 600,
              lineHeight: 1.4,
              textShadow: "2px 2px 4px rgba(0,0,0,0.8)",
            }}
          >
            {line}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
