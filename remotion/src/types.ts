/**
 * Python 파이프라인에서 전달하는 JSON 스키마.
 * 이 타입은 youtube-factory 전용이 아니라 범용으로 설계.
 */

export interface SceneData {
  index: number;
  narration: string;
  visualPrompt: string;
  duration: number; // 초 단위
  audioFile: string; // 절대 경로
  imageFile: string; // 절대 경로
}

export interface VideoData {
  title: string;
  description: string;
  tags: string[];
  scenes: SceneData[];
  config: VideoConfig;
}

export interface VideoConfig {
  fps: number;
  width: number;
  height: number;
  // 자막 설정
  subtitle: {
    enabled: boolean;
    fontSize: number;
    fontFamily: string;
    color: string;
    backgroundColor: string;
    position: "bottom" | "center" | "top";
  };
  // 전환 효과
  transition: {
    type: "fade" | "slide" | "wipe" | "none";
    durationFrames: number;
  };
  // 켄 번즈 (이미지 줌/패닝)
  kenBurns: {
    enabled: boolean;
    zoomRange: [number, number]; // [시작 배율, 끝 배율] ex: [1.0, 1.15]
  };
  // BGM
  bgm: {
    enabled: boolean;
    file: string;
    volume: number; // 0~1
    duckingVolume: number; // 나레이션 구간에서의 볼륨
  };
}

/** 기본 설정값 */
export const DEFAULT_CONFIG: VideoConfig = {
  fps: 30,
  width: 1920,
  height: 1080,
  subtitle: {
    enabled: true,
    fontSize: 48,
    fontFamily: "Malgun Gothic, sans-serif",
    color: "#FFFFFF",
    backgroundColor: "rgba(0,0,0,0.6)",
    position: "bottom",
  },
  transition: {
    type: "fade",
    durationFrames: 15, // 0.5초 @ 30fps
  },
  kenBurns: {
    enabled: true,
    zoomRange: [1.0, 1.12],
  },
  bgm: {
    enabled: false,
    file: "",
    volume: 0.3,
    duckingVolume: 0.1,
  },
};
