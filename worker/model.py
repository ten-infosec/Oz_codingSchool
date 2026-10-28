import threading
import uuid
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms


# ===== Model Info (담당: 엄태은) =====
# 사용 모델: DACON 흉부 X-ray 폐렴 분류 과제 E1b (ResNet18 전체 미세조정)
# 검증 성능: Recall(민감도) 0.9768, Accuracy 0.9799 → NFR-PRED-001(Recall ≥ 0.90) 충족
# 학습 코드: https://github.com/ten-infosec/dacon-chest-xray-pneumonia (02_Notebooks/Final_Pipeline.ipynb)


# DB ai_analysis_results.ai_model 칸에 저장할 모델 이름 (50자 이내)
# 같은 진료기록 + 같은 모델 이름이면 다시 예측하지 않고 저장된 결과를 쓴다 (REQ-PRED-001)
MODEL_NAME = "resnet18_e1b"

# 모델 파일 위치: worker/models/final_resnet18.pth
MODEL_PATH = Path(__file__).resolve().parent / "models" / "final_resnet18.pth"

# 히트맵 저장 위치: 프로젝트 최상위/media/heatmaps (app/main.py가 /media 주소로 연결해 둠)
MEDIA_ROOT = Path(__file__).resolve().parent.parent / "media"
HEATMAP_DIR = MEDIA_ROOT / "heatmaps"

# 폐렴 확률이 이 값 이상이면 폐렴으로 판정 (학습·리더보드 제출 때와 같은 기준)
THRESHOLD = 0.5

# 클래스 순서: 학습 데이터 라벨 0 = 정상(NORMAL), 1 = 폐렴(PNEUMONIA)
PNEUMONIA_INDEX = 1


# ===== Preprocessing (학습 때와 똑같이) =====


IMG_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# 학습 노트북의 전처리를 그대로 쓴다 (다르면 같은 모델이라도 결과가 달라진다)
# 1) 224×224로 크기 맞추기
# 2) 흑백 1채널 → 3채널로 복사 (ImageNet 사전학습 ResNet18이 3채널 입력을 받기 때문)
# 3) 0~255 픽셀을 0~1 텐서로
# 4) ImageNet 평균·표준편차로 정규화
TRANSFORM = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.Grayscale(num_output_channels=3),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])

# → 업로드된 X-ray를 학습 때와 같은 모양(1×3×224×224 텐서)으로 바꿀 준비를 하겠다


# ===== Result Type =====


@dataclass(frozen=True)
class PredictionResult:
    # 폐렴 확률이 THRESHOLD 이상이면 True
    is_pneumonia: bool
    # 판정한 쪽의 확률 × 100, 소수 둘째 자리 (예: 97.35) → DB Numeric(5, 2)
    confidence: float
    # Grad-CAM 히트맵 주소 (예: /media/heatmaps/3f2b....png)
    heatmap_url: str
    # 사용한 모델 이름 (= MODEL_NAME)
    ai_model: str

# → predict()가 돌려주는 값의 형식을 고정해서, API 담당자들이 이 칸 이름만 보고 쓸 수 있게 하겠다


# ===== Model Loading (서버에서 한 번만) =====


# 메모리에 올려 둔 모델 (처음에는 비어 있음)
_model: nn.Module | None = None

# 여러 요청이 동시에 들어와도 모델을 한 번만 불러오고, 예측도 한 번에 하나씩 하게 막는 잠금 장치
# (Grad-CAM은 모델 안에 잠깐 갈고리(hook)를 거는데, 두 요청이 동시에 걸면 결과가 섞일 수 있다)
_lock = threading.Lock()


def _build_model() -> nn.Module:
    # 학습 때와 같은 구조를 만든다
    # weights=None: 사전학습 가중치를 인터넷에서 받지 않는다 (어차피 아래에서 우리 가중치로 덮어씀)
    model = models.resnet18(weights=None)
    # 마지막 분류층을 1000개(ImageNet) → 2개(정상/폐렴)로 교체
    model.fc = nn.Linear(model.fc.in_features, 2)

    # state_dict(가중치 숫자 묶음)를 불러온다
    # map_location="cpu": GPU(cuda:0)에서 저장된 파일을 CPU에서 열기 위해
    # weights_only=True: 가중치 숫자만 읽고, 파일 안에 숨은 코드는 실행하지 않는다 (보안)
    state_dict = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
    model.load_state_dict(state_dict)

    # 평가 모드: 배치 정규화·드롭아웃을 예측용으로 고정 (안 하면 결과가 매번 달라진다)
    model.eval()
    return model

# → 구조를 만들고 학습된 가중치를 끼워 넣어, 예측 전용 모델을 준비하겠다


def get_model() -> nn.Module:
    # 이미 메모리에 있으면 그대로 쓰고, 처음 한 번만 파일에서 불러온다
    global _model
    if _model is None:
        with _lock:
            # 잠금을 기다리는 동안 다른 요청이 이미 불러왔을 수 있으니 한 번 더 확인
            if _model is None:
                _model = _build_model()
    return _model

# → 모델을 서버 메모리에 한 번만 올려 두고 계속 재사용하겠다 (NFR-PRED-002: 3초 이내 응답)


# ===== Grad-CAM Heatmap =====


def _grad_cam(model: nn.Module, x: torch.Tensor) -> tuple[torch.Tensor, np.ndarray]:
    """예측 결과(logits)와 Grad-CAM 지도(0~1, 224×224)를 함께 돌려준다."""
    activations = {}

    # layer4(마지막 합성곱 묶음)의 출력을 가로채 저장하는 갈고리
    def hook(_module, _inputs, output):
        activations["value"] = output

    handle = model.layer4.register_forward_hook(hook)
    try:
        # 기울기(gradient) 계산을 켠 상태로 예측
        with torch.enable_grad():
            logits = model(x)
            predicted = int(logits.argmax(dim=1).item())
            # 예측한 클래스 점수가 layer4 출력의 각 칸에 얼마나 민감한지(기울기) 계산
            grads = torch.autograd.grad(logits[0, predicted], activations["value"])[0]
    finally:
        # 갈고리는 쓰고 나면 반드시 뗀다 (안 떼면 요청마다 쌓인다)
        handle.remove()

    acts = activations["value"].detach()
    # 채널별 중요도 = 기울기의 평균
    weights = grads.mean(dim=(2, 3), keepdim=True)
    # 중요도로 가중합 → 음수는 버림(ReLU) → 폐렴 판단에 도움이 된 위치만 남김
    cam = F.relu((weights * acts).sum(dim=1, keepdim=True))
    # 7×7 지도를 입력 크기(224×224)로 키움
    cam = F.interpolate(cam, size=x.shape[-2:], mode="bilinear", align_corners=False)[0, 0]
    # 0~1 범위로 맞춤
    cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
    return logits.detach(), cam.numpy()

# → 모델이 X-ray의 어느 부분을 보고 판정했는지 0~1 지도로 계산하겠다 (학습 노트북 8번 셀과 같은 방식)


def _jet_colormap(cam: np.ndarray) -> np.ndarray:
    # 0(파랑) → 0.5(초록·노랑) → 1(빨강)으로 칠한다 (matplotlib 없이 직접 계산)
    r = np.clip(1.5 - np.abs(4 * cam - 3), 0, 1)
    g = np.clip(1.5 - np.abs(4 * cam - 2), 0, 1)
    b = np.clip(1.5 - np.abs(4 * cam - 1), 0, 1)
    return (np.stack([r, g, b], axis=-1) * 255).astype(np.uint8)


def _save_heatmap(original: Image.Image, cam: np.ndarray) -> str:
    # 원본 X-ray(흑백)를 224×224 컬러로 맞춤
    base = original.convert("RGB").resize((IMG_SIZE, IMG_SIZE))
    # 지도를 색으로 칠한 이미지
    color = Image.fromarray(_jet_colormap(cam))
    # 원본 60% + 색 40%로 겹치기
    overlay = Image.blend(base, color, alpha=0.4)

    # 랜덤 파일 이름으로 저장 (덮어쓰기·경로 조작 방지, X-ray 저장 규칙과 같음)
    HEATMAP_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.png"
    overlay.save(HEATMAP_DIR / filename)
    return f"/media/heatmaps/{filename}"

# → 원본 위에 색 지도를 겹친 히트맵 이미지를 저장하고 주소를 돌려주겠다


# ===== Predict (API에서 부르는 함수) =====


def predict(image_path: str | Path) -> PredictionResult:
    """X-ray 파일 경로를 받아 폐렴 예측 결과를 돌려준다.

    - 파일이 없으면 FileNotFoundError
    - 계산이 무거운 동기 함수이므로 API에서는 run_in_threadpool(predict, path)로 부른다
    """
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"X-ray 이미지가 없습니다: {path}")

    model = get_model()

    # 이미지 열기 → 흑백(L)으로 (학습 때와 같음)
    with Image.open(path) as img:
        original = img.convert("L")
    # 전처리 후 배치 차원 추가: (3, 224, 224) → (1, 3, 224, 224)
    x = TRANSFORM(original).unsqueeze(0)

    # 한 번에 하나씩 예측 (Grad-CAM 갈고리가 섞이지 않게)
    with _lock:
        logits, cam = _grad_cam(model, x)

    # 두 클래스 점수를 확률로 바꾸고, 폐렴 쪽 확률을 꺼냄
    prob_pneumonia = float(torch.softmax(logits, dim=1)[0, PNEUMONIA_INDEX])
    is_pneumonia = prob_pneumonia >= THRESHOLD
    # confidence = 판정한 쪽의 확률 (폐렴이면 폐렴 확률, 정상이면 정상 확률)
    confidence = prob_pneumonia if is_pneumonia else 1 - prob_pneumonia

    return PredictionResult(
        is_pneumonia=is_pneumonia,
        confidence=round(confidence * 100, 2),
        heatmap_url=_save_heatmap(original, cam),
        ai_model=MODEL_NAME,
    )

# → 이미지를 학습 때와 같게 전처리해 예측하고, 폐렴 여부·확신도·히트맵 주소·모델 이름을 묶어 돌려주겠다
