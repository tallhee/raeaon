sudo apt-get -qq update && sudo apt-get -qq install -y tesseract-ocr tesseract-ocr-kor poppler-utils >/dev/null
pip -q install pyhwp 2>/dev/null
python3 probe/probe3.py
rm -f probe/out3/A1*   # 원본 첨부는 저장소에 올리지 않음
