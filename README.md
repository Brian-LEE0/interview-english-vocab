# 면접영어 어원 단어장 (mensetsu-tango)

IT 면접 영어 단어를 어원(접두사 + 어근 + 접미사)으로 쪼개서 외우는 30일 단어장. 하루 100단어, 예문은 면접에서 그대로 말할 수 있는 답변.

## 쓰는 법

`dist/index.html` 을 브라우저로 엽니다. 휴대폰에서 쓰려면 이 파일 하나만 옮기면 됩니다.

## 파일

| 경로 | 내용 |
|---|---|
| [PLAN.md](PLAN.md) | 기준 문서 — 30일 구성, 난이도·분야 비율, 데이터 형식, 화면 |
| [data/GUIDE.md](data/GUIDE.md) | 단어 데이터 작성 규칙 |
| `data/parts/dayDD-A~D.json` | 세트별 원본 데이터 |
| `data/dayDD.json` | 합쳐서 검사한 하루 데이터 |
| `app/index.html` | 웹 단어장 화면 코드 |
| `dist/index.html` | 데이터를 넣은 완성본 (이 파일을 엶) |
| `design/mockup.html` | 디자인 시안 |

## 다시 만들기

```bash
python scripts/build_data.py
python scripts/build_app.py
```

`build_data.py` 는 세트당 25개, 난이도·분야 숫자, 대표 단어, 날짜 사이 중복을 검사하고 오류가 있으면 멈춥니다.
