import sys
import time

from worker.model import MODEL_NAME, predict


# ===== Model Check (담당: 엄태은) =====
# 서버 없이 모델만 확인하는 스크립트
# 실행: python -m worker.check_model <X-ray 이미지 경로>


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python -m worker.check_model <X-ray 이미지 경로>")
        sys.exit(1)

    # 첫 예측: 모델 불러오기 + 예측 (시간이 조금 더 걸림)
    start = time.perf_counter()
    result = predict(sys.argv[1])
    first = time.perf_counter() - start

    # 두 번째 예측: 모델이 이미 메모리에 있으므로 예측 시간만 걸림
    start = time.perf_counter()
    predict(sys.argv[1])
    second = time.perf_counter() - start

    print(f"모델: {MODEL_NAME}")
    print(f"폐렴 여부: {result.is_pneumonia} | confidence: {result.confidence}%")
    print(f"히트맵: {result.heatmap_url}")
    print(f"첫 예측 {first:.2f}초 (모델 불러오기 포함) / 두 번째 예측 {second:.2f}초")
