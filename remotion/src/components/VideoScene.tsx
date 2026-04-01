import React from "react";
import { AbsoluteFill, Audio, Sequence, useVideoConfig } from "remotion";
import { SceneData, VideoConfig, DEFAULT_CONFIG } from "../types";
import { KenBurnsImage } from "./KenBurnsImage";
import { Subtitle } from "./Subtitle";
import { SceneTransition } from "./SceneTransition";

interface Props {
  scene: SceneData;
  config: VideoConfig;
}

/**
 * 개별 장면 컴포넌트.
 * 이미지(켄번즈) + 오디오 + 자막을 조합.
 */
export const VideoScene: React.FC<Props> = ({ scene, config }) => {
  const { fps } = useVideoConfig();
  const cfg = { ...DEFAULT_CONFIG, ...config };

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* 전환 효과 */}
      <SceneTransition
        type={cfg.transition.type}
        durationFrames={cfg.transition.durationFrames}
      >
        {/* 배경 이미지 (켄 번즈) */}
        {cfg.kenBurns.enabled ? (
          <KenBurnsImage
            src={scene.imageFile}
            zoomStart={cfg.kenBurns.zoomRange[0]}
            zoomEnd={cfg.kenBurns.zoomRange[1]}
          />
        ) : (
          <AbsoluteFill>
            <img
              src={scene.imageFile}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>
        )}

        {/* 자막 */}
        {cfg.subtitle.enabled && (
          <Subtitle
            text={scene.narration}
            fontSize={cfg.subtitle.fontSize}
            fontFamily={cfg.subtitle.fontFamily}
            color={cfg.subtitle.color}
            backgroundColor={cfg.subtitle.backgroundColor}
            position={cfg.subtitle.position}
          />
        )}
      </SceneTransition>

      {/* 나레이션 오디오 */}
      <Audio src={scene.audioFile} volume={1} />
    </AbsoluteFill>
  );
};
