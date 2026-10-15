# 래아온 비교노트

잠실래미안아이파크 입주자대표회의 업무를 다른 단지의 공고·규정과 비교해 보기 위한 공개 자료실입니다.

## 다루는 주제

| 주제 | 비교 항목 |
|---|---|
| 주차규정 | 공공개방시설 이용자 주차 제공 여부, 방문차량 요금, 세대 면적별 주차대수·요금 |
| 커뮤니티 운영규정 | 운영시간, 요금, 입장 횟수 |
| 커뮤니티 식당 | 업체 선정 방식, 운영시간, 요금 |
| 입대의·선관위 | 공고 모아보기 |

비교 단지: 서울 2020년 이후 입주 단지, 송파·강남·서초·강동구 1,500세대 이상 대단지 (`config/sources.json` 에서 조정)

## 구조

```
config/sources.json         주제 키워드, 비교 단지 조건, API 주소
scripts/collect.py          수집 스크립트 (표준 라이브러리만 사용)
.github/workflows/collect.yml  매일 06:47(KST) 자동 수집 + 수동 실행
docs/                       GitHub Pages 사이트
  data/rules.json           ← 원문 확인 후 직접 정리하는 규정 비교표
  data/notices.json         자동 수집: K-apt 입찰공고 중 주제 관련 공고
  data/complexes.json       자동 수집: 단지 기본정보 (입주연도·세대수)
  data/presale.json         자동 수집: 청약홈 서울 입주자모집공고
  data/run_status.json      자동 수집: 출처별 성공/실패
```

## 처음 설정 (한 번만)

1. **공공데이터포털 인증키**: [data.go.kr](https://www.data.go.kr)에서 아래 3개를 활용신청합니다. 보통 자동승인이며, 키 하나로 모두 쓸 수 있습니다.
   - 국토교통부_공동주택 입찰공고 정보제공 서비스
   - 국토교통부_공동주택 기본 정보제공 서비스
   - 한국부동산원_청약홈 분양정보 조회 서비스
2. **Secret 등록**: 저장소 Settings → Secrets and variables → Actions → New repository secret
   이름 `DATA_GO_KR_API_KEY`, 값은 마이페이지의 **일반 인증키(Decoding)**.
3. **Pages 켜기**: Settings → Pages → Source: Deploy from a branch → `main` / `/docs`.
4. **첫 수집**: Actions → 공고 수집 → Run workflow. 결과는 사이트의 '수집 상태' 탭에서 확인합니다.

## 규정 비교표 채우기

`docs/data/rules.json` 의 `complexes` 배열에 단지를 추가합니다. 원문에서 확인한 값만 적고, 모르는 칸은 `null` 로 둡니다. 항목마다 `source`(원문 링크)와 `checked`(확인일)를 남겨 주세요.

## 알려진 한계

- **서울시 공동주택마당(openapt)**: 공개 API가 없어 자동 수집에서 빠져 있습니다. 찾은 공고는 rules.json의 `source` 링크로 남깁니다.
- **K-apt 입찰공고 원문**: API에는 개별 공고 상세 링크가 없어 목록 페이지로 연결됩니다.
- API 주소나 필드명이 바뀌면 '수집 상태'에 실패로 표시되며, `config/sources.json`의 `endpoints`만 고치면 됩니다.
