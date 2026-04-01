import React from "react";
import { Composition, staticFile } from "remotion";
import { YouTubeVideo } from "./YouTubeVideo";
import { VideoData, DEFAULT_CONFIG } from "./types";

/**
 * Remotion 루트 - 컴포지션 등록.
 *
 * 렌더링 시 --props 플래그로 JSON 데이터를 전달받음:
 *   npx remotion render src/index.ts YouTubeVideo --props=./data.json -o output.mp4
 */

// 기본 프리뷰용 샘플 데이터
const sampleData: VideoData = {
  title: "샘플 영상",
  description: "Remotion 테스트 영상",
  tags: ["test"],
  scenes: [
    {
      index: 0,
      narration: "안녕하세요, 첫 번째 장면입니다.",
      visualPrompt: "A beautiful sunrise",
      duration: 5,
      audioFile: "",
      imageFile: "",
    },
  ],
  config: DEFAULT_CONFIG,
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="YouTubeVideo"
        component={YouTubeVideo}
        durationInFrames={300} // props에서 동적 계산됨
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{ data: sampleData }}
        calculateMetadata={async ({ props }) => {
          const { data } = props;
          const fps = data.config?.fps || 30;
          const totalDuration = data.scenes.reduce(
            (sum: number, s: { duration: number }) => sum + s.duration,
            0
          );
          return {
            durationInFrames: Math.ceil(totalDuration * fps),
            fps,
            width: data.config?.width || 1920,
            height: data.config?.height || 1080,
          };
        }}
      />
    </>
  );
};
