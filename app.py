from datetime import datetime
import os
import re
import fitz  # PyMuPDF
import pandas as pd
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import streamlit as st

# === Tesseractのインストール場所の自動判別設定 ===
if os.name == "nt":
  pytesseract.pytesseract.tesseract_cmd = (
      r"C:\Program Files\Tesseract-OCR\tesseract.exe"
  )

# ページ全体のレイアウトをワイドに設定
st.set_page_config(
    page_title="お仕事便利ツールボックス",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🛠️ 業務ツールボックス")
st.write(
    "請求書文字起こし、PDF切り取り、および4連伝票対応の定型フォーマットCSV化ツール"
)

# --- タブメニューの作成 ---
tab1, tab2, tab3 = st.tabs([
    "📄 請求書文字起こし (画像・PDF・表対応)",
    "✂️ カスタムトリミングツール",
    "📊 4連伝票OCR ➔ CSV自動変換",
])

# ==========================================
# タブ1：請求書文字起こし（画像 ＆ PDF ＆ 表対応）
# ==========================================
with tab1:
  st.header("📄 請求書文字起こし（画像 ＆ PDF）")
  st.write("画像ファイル、またはPDFファイルをアップロードして文字を読み取ります。")

  with st.expander(
      "ℹ 【初めての方へ】Tesseract OCRのインストール・準備について"
  ):
    st.markdown("""
        このOCR機能を使うには、WindowsパソコンにOCRエンジン本体のインストールが必要です。
        1. 以下の公式ページからインストーラーをダウンロードしてください。
            * **[Tesseract OCR ダウンロード元 (GitHub Wiki)](https://github.com/UB-Mannheim/tesseract/wiki)**
        2. インストール途中の画面で、必ず **`Japanese`（日本語言語データ）** にチェックを入れてインストールしてください。
        3. 標準のインストール先（`C:\Program Files\Tesseract-OCR\tesseract.exe`）に配置されます。
        """)

  uploaded_file = st.file_uploader(
      "ファイルを選択してください",
      type=["png", "jpg", "jpeg", "pdf"],
      key="ocr_file",
  )

  if uploaded_file is not None:
    file_extension = uploaded_file.name.split(".")[-1].lower()
    st.write("---")
    ocr_mode = st.selectbox(
        "📊 読み取りモード（表やレイアウトに合わせて調整）",
        [
            "表・ブロック優先 (PSM 6) ※表組みにおすすめ",
            "標準 (Auto)",
            "1列テキスト優先 (PSM 4)",
        ],
    )

    if "PSM 6" in ocr_mode:
      custom_config = r"--psm 6"
    elif "PSM 4" in ocr_mode:
      custom_config = r"--psm 4"
    else:
      custom_config = r""

    st.write("---")

    if file_extension in ["png", "jpg", "jpeg"]:
      image = Image.open(uploaded_file)
      st.image(image, caption="アップロードされた画像", use_column_width=True)

      if st.button("画像から文字を読み取る", key="btn_img"):
        with st.spinner("画像から文字を解析中..."):
          img_gray = image.convert("L")
          text = pytesseract.image_to_string(
              img_gray, lang="jpn+eng", config=custom_config
          )
          st.subheader("📝 読み取り結果")
          st.text_area("抽出されたテキスト", text, height=300)

    elif file_extension == "pdf":
      st.info("PDFファイルがアップロードされました。全ページの文字を読み取ります。")

      if st.button("PDFの文字を読み取る", key="btn_pdf"):
        with st.spinner("PDFを解析中..."):
          uploaded_file.seek(0)
          doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
          all_text = ""

          for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=400)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_gray = img.convert("L")

            page_text = pytesseract.image_to_string(
                img_gray, lang="jpn+eng", config=custom_config
            )
            all_text += (
                f"--- 【 第 {page_num + 1} ページ 】 ---\n{page_text}\n\n"
            )

          st.subheader("📝 読み取り結果（全ページ）")
          st.text_area("抽出されたテキスト", all_text, height=400)


# ==========================================
# タブ2：カスタムトリミングツール（ページ指定対応版）
# ==========================================
with tab2:
  st.header("✂️ カスタムトリミングツール")
  st.write("2つのPDF（上側・下側）の**対象ページ**と必要な部分を指定してカスタム結合します。")

  col1, col2 = st.columns(2)
  with col1:
    pdf_top_file = st.file_uploader(
        "① 上側に配置するPDF", type=["pdf"], key="custom_top"
    )
  with col2:
    pdf_bottom_file = st.file_uploader(
        "② 下側に配置するPDF", type=["pdf"], key="custom_bottom"
    )

  st.write("---")
  st.subheader("📄 ページ指定 ＆ 切り抜き・レイアウト設定")

  # ページ選択のための事前読み込みチェック
  top_total_pages = 1
  bottom_total_pages = 1

  if pdf_top_file is not None:
    pdf_top_file.seek(0)
    doc_t = fitz.open(stream=pdf_top_file.read(), filetype="pdf")
    top_total_pages = len(doc_t)

  if pdf_bottom_file is not None:
    pdf_bottom_file.seek(0)
    doc_b = fitz.open(stream=pdf_bottom_file.read(), filetype="pdf")
    bottom_total_pages = len(doc_b)

  tc1, tc2 = st.columns(2)
  with tc1:
    st.markdown("### ① 上側ファイルの指定")
    top_page_idx = st.number_input(
        "抽出するページ番号", min_value=1, max_value=top_total_pages, value=1, step=1, key="t_page"
    )
    st.write(f"(総ページ数: {top_total_pages} ページ)")
    
    top_dir = st.selectbox(
        "基準位置", ["上から残す", "下から残す"], key="t_dir"
    )
    top_pct = st.slider(
        "残す割合 (%)",
        min_value=10,
        max_value=100,
        value=50,
        step=5,
        key="t_pct",
    )

  with tc2:
    st.markdown("### ② 下側ファイルの指定")
    bottom_page_idx = st.number_input(
        "抽出するページ番号", min_value=1, max_value=bottom_total_pages, value=1, step=1, key="b_page"
    )
    st.write(f"(総ページ数: {bottom_total_pages} ページ)")

    bottom_dir = st.selectbox(
        "基準位置", ["上から残す", "下から残す"], key="b_dir"
    )
    bottom_pct = st.slider(
        "残す割合 (%)",
        min_value=10,
        max_value=100,
        value=50,
        step=5,
        key="b_pct",
    )

  st.write("---")
  c1, c2 = st.columns(2)
  with c1:
    orientation = st.selectbox(
        "用紙の向き", ["A4 縦 (Portrait)", "A4 横 (Landscape)"], key="custom_ori"
    )
  with c2:
    layout_ratio = st.selectbox(
        "上下の配置比率", ["50 / 50", "40 / 60", "60 / 40"], key="custom_rat"
    )

  if st.button("カスタムツールを実行！", type="primary"):
    if pdf_top_file is not None and pdf_bottom_file is not None:
      with st.spinner("指定ページをトリミング＆結合中..."):
        if "縦" in orientation:
          page_w, page_h = 595.27, 841.89
        else:
          page_w, page_h = 841.89, 595.27

        if layout_ratio == "50 / 50":
          split_rate = 0.5
        elif layout_ratio == "40 / 60":
          split_rate = 0.4
        else:
          split_rate = 0.6

        h_top_area = page_h * split_rate
        h_bottom_area = page_h - h_top_area

        def pdf_to_cropped_image(pdf_file, page_num, direction, pct):
          pdf_file.seek(0)
          doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
          page = doc[page_num - 1]  # 0始まりのインデックスに変換
          pix = page.get_pixmap(dpi=400)
          img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

          w, h = img.size
          target_height = int(h * (pct / 100.0))

          if direction == "上から残す":
            box = (0, 0, w, target_height)
          else:
            box = (0, h - target_height, w, h)

          return img.crop(box)

        img_top_cropped = pdf_to_cropped_image(
            pdf_top_file, top_page_idx, top_dir, top_pct
        )
        img_bottom_cropped = pdf_to_cropped_image(
            pdf_bottom_file, bottom_page_idx, bottom_dir, bottom_pct
        )

        out_doc = fitz.open()
        new_page = out_doc.new_page(width=page_w, height=page_h)

        temp_top_path = "temp_top.png"
        temp_bottom_path = "temp_bottom.png"
        img_top_cropped.save(temp_top_path)
        img_bottom_cropped.save(temp_bottom_path)

        rect_top = fitz.Rect(0, 0, page_w, h_top_area)
        new_page.insert_image(rect_top, filename=temp_top_path)

        rect_bottom = fitz.Rect(
            0, h_top_area, page_w, h_top_area + h_bottom_area
        )
        new_page.insert_image(rect_bottom, filename=temp_bottom_path)

        output_pdf_bytes = out_doc.convert_to_pdf()

        st.success("カスタムガッチャンコが完了しました！")
        st.download_button(
            label="📥 カスタムPDFをダウンロード",
            data=output_pdf_bytes,
            file_name="custom_combined.pdf",
            mime="application/pdf",
        )
    else:
      st.warning("上下のPDFファイルを両方ともアップロードしてください。")


# ==========================================
# タブ3：4連伝票OCR ➔ CSV自動変換
# ==========================================
with tab3:
  st.header("📊 4連伝票OCR ➔ CSV自動変換")
  st.write(
      "品名(1行目スキップ), 数量(小数第1位), 単価(ドット排除＆小数第1位), 販売管理Noに**伝票の日付**を反映して抽出します。"
  )

  pdf_csv_file = st.file_uploader(
      "4連伝票PDFファイルを選択してください", type=["pdf"], key="csv_pdf_v3"
  )

  if pdf_csv_file is not None:
    pdf_csv_file.seek(0)
    doc_csv = fitz.open(stream=pdf_csv_file.read(), filetype="pdf")
    total_pages = len(doc_csv)

    st.info(f"📄 読み込んだPDFの総ページ数: **{total_pages} ページ**")

    st.write("---")
    st.subheader("📌 読み込むページの範囲指定")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
      start_page = st.number_input(
          "開始ページ", min_value=1, max_value=total_pages, value=1, step=1
      )
    with col_p2:
      end_page = st.number_input(
          "終了ページ",
          min_value=1,
          max_value=total_pages,
          value=min(total_pages, total_pages),
          step=1,
      )

    if start_page > end_page:
      st.error("エラー: 開始ページは終了ページ以下にしてください。")
    else:
      if st.button("データ抽出＆CSV変換を実行", type="primary"):
        with st.spinner("データを抽出し、伝票日付から販売管理Noを自動構築中..."):
          extracted_rows = []

          for p_num in range(start_page - 1, end_page):
            page = doc_csv[p_num]
            pix = page.get_pixmap(dpi=400)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            w, h = img.size
            block_w = w
            block_h = int(h * 0.28)
            img_top_block = img.crop((0, 0, block_w, block_h))

            y_top_item = int(block_h * 0.695)
            y_bottom_item = int(block_h * 0.815)
            y_top_num = int(block_h * 0.725)
            y_bottom_num = int(block_h * 0.82)

            box_item = (
                int(block_w * 0.01),
                y_top_item,
                int(block_w * 0.265),
                y_bottom_item,
            )
            box_qty = (
                int(block_w * 0.47),
                y_top_num,
                int(block_w * 0.51),
                y_bottom_num,
            )
            box_price = (
                int(block_w * 0.65),
                y_top_num,
                int(block_w * 0.735),
                y_bottom_num,
            )

            img_item = img_top_block.crop(box_item)
            img_qty = img_top_block.crop(box_qty)
            img_price = img_top_block.crop(box_price)

            def ocr_item_skip_first_line(cropped_img):
              new_w = int(cropped_img.width * 2)
              new_h = int(cropped_img.height * 2)
              zoomed = cropped_img.resize(
                  (new_w, new_h), Image.Resampling.LANCZOS
              )
              gray = zoomed.convert("L")
              enhanced = ImageOps.autocontrast(gray, cutoff=2)
              sharpened = enhanced.filter(ImageFilter.SHARPEN)

              raw_text = pytesseract.image_to_string(
                  sharpened, lang="jpn+eng", config=r"--psm 6"
              )
              lines = [
                  line.strip()
                  for line in raw_text.split("\n")
                  if line.strip()
              ]

              if len(lines) > 1:
                return " ".join(lines[1:])
              elif len(lines) == 1:
                return lines[0]
              else:
                return ""

            def format_to_decimal_1(raw_str):
              clean_str = re.sub(r"[^\d.]", "", raw_str)
              if not clean_str:
                return ""
              try:
                val = float(clean_str)
                return f"{val:.1f}"
              except ValueError:
                return clean_str

            def format_price_as_decimal_1(raw_str):
              clean_str = re.sub(r"[^\d]", "", raw_str)
              if not clean_str:
                return ""
              try:
                val = float(clean_str) / 10.0
                return f"{val:.1f}"
              except ValueError:
                return clean_str

            def ocr_qty(cropped_img):
              zoomed = cropped_img.resize(
                  (cropped_img.width * 3, cropped_img.height * 3),
                  Image.Resampling.LANCZOS,
              )
              gray = zoomed.convert("L")
              enhanced = ImageOps.autocontrast(gray, cutoff=2)
              text = (
                  pytesseract.image_to_string(
                      enhanced, lang="eng", config=r"--psm 7"
                  )
                  .strip()
                  .replace("\n", " ")
              )
              text = (
                  text.replace("Q", "0")
                  .replace("q", "0")
                  .replace("O", "0")
                  .replace("o", "0")
              )
              return format_to_decimal_1(text)

            def ocr_price(cropped_img):
              zoomed = cropped_img.resize(
                  (cropped_img.width * 3, cropped_img.height * 3),
                  Image.Resampling.LANCZOS,
              )
              gray = zoomed.convert("L")
              enhanced = ImageOps.autocontrast(gray, cutoff=2)
              text = (
                  pytesseract.image_to_string(
                      enhanced, lang="eng", config=r"--psm 7"
                  )
                  .strip()
                  .replace("\n", " ")
              )
              text = (
                  text.replace("Q", "0")
                  .replace("q", "0")
                  .replace("O", "0")
                  .replace("o", "0")
                  .replace(",", "")
              )
              return format_price_as_decimal_1(text)

            item_text = ocr_item_skip_first_line(img_item)
            qty_text = ocr_qty(img_qty)
            price_text = ocr_price(img_price)

            page_full_text = pytesseract.image_to_string(
                img_top_block.convert("L"), lang="jpn+eng", config=r"--psm 6"
            )

            order_no = ""
            date_val = ""

            for line in page_full_text.split("\n"):
              if not order_no:
                m_ord = re.search(r"(\d{4}[-\s]?\d{4,})", line)
                if m_ord:
                  raw_ord = m_ord.group(1).replace(" ", "").replace("-", "")
                  if len(raw_ord) >= 8:
                    order_no = f"{raw_ord[:4]}-{raw_ord[4:]}"
                  else:
                    order_no = raw_ord

              if not date_val:
                m_date_2 = re.search(
                    r"\b(\d{2})[/.-](\d{1,2})[/.-](\d{1,2})\b", line
                )
                if m_date_2:
                  yy_d, mm, dd = m_date_2.groups()
                  date_val = f"20{yy_d}/{int(mm):02d}/{int(dd):02d}"
                else:
                  m_date_4 = re.search(
                      r"(\d{2,4}[/年]\d{1,2}[/月]\d{1,2}日?)", line
                  )
                  if m_date_4:
                    date_val = m_date_4.group(1)