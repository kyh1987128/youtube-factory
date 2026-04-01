import React from "react";
import { AbsoluteFill, Audio, Sequence, useVideoConfig } from "remotion";
import { VideoData, DEFAULT_CONFIG } from "./types";
import { VideoScene } from "./components/VideoScene";

/**
 * 메인 컴포지션 - 모든 장면을 시퀀스로 조합.
 * Python 파이프라인에서 전달한 JSON 데이터로 구동.
 */
export const YouTubeVideo: React.FC<{ data: VideoData }> = ({ data }) => {
  const { fps } = useVideoConfig();
  const config = { ...DEFAULT_CONFIG, ...data.config };

  // 각 장면의 프레임 수 계산
  const scenesWithFrames = data.scenes.map((scene) => ({
    ...scene,
    durationInFrames: Math.ceil(scene.duration * fps),
  }));

  // 장면별 시작 프레임 계산
  let currentFrame = 0;
  const sequences = scenesWithFrames.map((scene) => {
    const from = currentFrame;
    currentFrame += scene.durationInFrames;
    return { scene, from, durationInFrames: scene.durationInFrames };
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* 장면 시퀀스 */}
      {sequences.map(({ scene, from, durationInFrames }) => (
        <Sequence
          key={scene.index}
          from={from}
          durationInFrames={durationInFrames}
          name={`Scene ${scene.index + 1}`}
        >
          <VideoScene scene={scene} config={config} />
        </Sequence>
      ))}

      {/* BGM (전체 영상에 걸쳐) */}
      {config.bgm.enabled && config.bgm.file && (
        <Audio src={config.bgm.file} volume={config.bgm.volume} loop />
      )}
    </AbsoluteFill>
  );
};
