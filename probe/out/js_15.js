<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, interactive-widget=resizes-content" />
    <!-- 공개 제품 소개는 별도 랜딩에서 제공하며 개인 작업 화면은 색인하지 않는다. -->
    <meta name="robots" content="noindex, nofollow" />
    <title>애니톡</title>
    <meta name="description" content="스스로 판단하고, 도구를 활용하고, 업무를 해결합니다. Thinks for itself, uses tools, and gets the work done." />

    <!-- OG 태그는 여기 정적으로 둔다. 카카오톡·슬랙 크롤러는 JS 를 안 돌리므로
         Vue 안에서 head 에 붙이면 크롤러에게 보이지 않는다. og:url·og:image 는
         절대 URL 이어야 해서 VITE_PUBLIC_ORIGIN 을 빌드 때 치환한다(비면 상대경로가
         돼 미리보기 이미지가 안 뜬다 — .env 를 볼 것). -->
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="애니톡" />
    <meta property="og:title" content="애니톡 anytalk" />
    <meta property="og:description" content="스스로 판단하고, 도구를 활용하고, 업무를 해결합니다. Thinks for itself, uses tools, and gets the work done." />
    <meta property="og:url" content="https://anytalk.com/chat/" />
    <meta property="og:image" content="https://anytalk.com/chat/og-image.png" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <!-- 정적 HTML 하나라 크롤러별 언어 선택은 못 한다(카카오·슬랙은 Accept-Language 를
         안 본다). 그래서 설명은 한 문장에 한·영을 같이 싣고, locale 은 둘을 선언한다. -->
    <meta property="og:locale" content="ko_KR" />
    <meta property="og:locale:alternate" content="en_US" />
    <!-- X·Discord 가 미리보기를 큰 이미지로 그릴지 정하는 값. 제목·설명·이미지는
         og:* 로 폴백되므로 twitter:* 로 다시 적지 않는다 — 같은 사실의 사본이 된다. -->
    <meta name="twitter:card" content="summary_large_image" />
    <script type="module" crossorigin src="/assets/index-DoNwYPYT.js"></script>
    <link rel="stylesheet" crossorigin href="/assets/index-B3zVS8lJ.css">
  </head>
  <body>
    <div id="app"></div>
  </body>
</html>
