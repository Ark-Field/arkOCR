from datetime import datetime
import re
import fitz  # PyMuPDF
import pandas as pd
from PIL import Image, ImageOps, ImageFilter
import pytesseract
import streamlit as st

# === Tesseractのインストール場所を指定 ===
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# ページ全体のレイアウトをワイドに設定
st.set_page_config(
    page_title="お仕事便利ツールボックス",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🛠️ 業務お助けツールボックス")
st.write(
    "OCR文字起こし、PDFガッチャンコ、および4連伝票対応の定型フォーマットCSV化ツール"
)

# --- タブメニューの作成 ---
tab1, tab2, tab3 = st.tabs([
    "📄 OCR文字起こし (画像・PDF・表対応)",
    "✂️ カスタムトリミング＆ガッチャンコ",
    "📊 4連伝票OCR ➔ CSV自動変換",
])

# ==========================================
# タブ1：OCR文字起こし（画像 ＆ PDF ＆ 表対応）
# ==========================================
with tab1:
  st.header("📄 OCR文字起こし（画像 ＆ PDF）")
  st.write("画像ファイル、またはPDFファイルをアップロードして文字を読み取ります。")

  with st.expander(
      "ℹ️ 【初めての方へ】Tesseract OCRのインストール・準備について"
  ):
    st.markdown("""
        このOCR機能を使うには、WindowsパソコンにOCRエンジン本体のインストールが必要です。
        1. 以下の公式ページからインストーラーをダウンロードしてください。
           * **[Tesseract OCR ダウンロード元 (GitHub Wiki)](https://github.com/UB-Mannheim/tesseract/wiki)**
        2. インストール途中の画面で、必ず **`Japanese`（日本語言語データ）** にチェックを入れてインストールしてください。
        3. 標準のインストール先（`C:\\Program Files\\Tesseract-OCR\\tesseract.exe`）に配置されます。
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
# タブ2：カスタムトリミング付きPDFガッチャンコ
# ==========================================
with tab2:
  st.header("✂️ カスタムトリミング＆ガッチャンコ")
  st.write("2つのPDFの必要な部分を指定してカスタム結合します。")

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
  st.subheader("📐 切り抜き・レイアウト設定")

  tc1, tc2 = st.columns(2)
  with tc1:
    st.markdown("### ① 上側ファイルの切り抜き")
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
    st.markdown("### ② 下側ファイルの切り抜き")
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

  if st.button("カスタムガッチャンコを実行！", type="primary"):
    if pdf_top_file is not None and pdf_bottom_file is not None:
      with st.spinner("PDFをトリミング＆結合中..."):
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

        def pdf_to_cropped_image(pdf_file, direction, pct):
          pdf_file.seek(0)
          doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
          page = doc[0]
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
            pdf_top_file, top_dir, top_pct
        )
        img_bottom_cropped = pdf_to_cropped_image(
            pdf_bottom_file, bottom_dir, bottom_pct
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
# タブ3：4連伝票OCR ➔ CSV自動変換（伝票日付連動型・販売管理No自動生成版）
# ==========================================
with tab3:
  st.header("📊 4連伝票OCR ➔ CSV自動変換 (伝票日付連動・販売管理No生成)")
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

            # 1. 4連伝票の上から1段目（高さの約28%）を切り出す（100%の基準）
            w, h = img.size
            block_w = w
            block_h = int(h * 0.28)
            img_top_block = img.crop((0, 0, block_w, block_h))

            # 2. 座標の切り抜き範囲を設定
            # 品名用 上下: 69.5% 〜 81.5%
            y_top_item = int(block_h * 0.695)
            y_bottom_item = int(block_h * 0.815)

            # 数量・単価用 上下: 72.5% 〜 82%
            y_top_num = int(block_h * 0.725)
            y_bottom_num = int(block_h * 0.82)

            # 品名: 左 1% 〜 26.5%
            box_item = (
                int(block_w * 0.01),
                y_top_item,
                int(block_w * 0.265),
                y_bottom_item,
            )
            # 数量: 左 47% 〜 51.0%
            box_qty = (
                int(block_w * 0.47),
                y_top_num,
                int(block_w * 0.51),
                y_bottom_num,
            )
            # 単価: 左 65% 〜 73.5%
            box_price = (
                int(block_w * 0.65),
                y_top_num,
                int(block_w * 0.735),
                y_bottom_num,
            )

            img_item = img_top_block.crop(box_item)
            img_qty = img_top_block.crop(box_qty)
            img_price = img_top_block.crop(box_price)

            # 品名専用（1行目スキップ関数）
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

            # 数量整形関数（小数点第1位）
            def format_to_decimal_1(raw_str):
              clean_str = re.sub(r"[^\d.]", "", raw_str)
              if not clean_str:
                return ""
              try:
                val = float(clean_str)
                return f"{val:.1f}"
              except ValueError:
                return clean_str

            # 単価整形関数（ドット全排除＆下1桁を小数第1位）
            def format_price_as_decimal_1(raw_str):
              clean_str = re.sub(r"[^\d]", "", raw_str)
              if not clean_str:
                return ""
              try:
                val = float(clean_str) / 10.0
                return f"{val:.1f}"
              except ValueError:
                return clean_str

            # 数量用OCR
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

            # 単価用OCR
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

            # ページ全体から注文番号や日付を取得
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
                m_date_2 = re.search(r"\b(\d{2})[/.-](\d{1,2})[/.-](\d{1,2})\b", line)
                if m_date_2:
                  yy_d, mm, dd = m_date_2.groups()
                  date_val = f"20{yy_d}/{int(mm):02d}/{int(dd):02d}"
                else:
                  m_date_4 = re.search(r"(\d{2,4}[/年]\d{1,2}[/月]\d{1,2}日?)", line)
                  if m_date_4:
                    date_val = m_date_4.group(1)

            # ★ 抽出した伝票の日付から販売管理Noを動的に生成する
            # 例: date_val が "2026/09/05" なら、yy="26", mm="09", dd="05" → "2690905"
            m_parsed_date = re.search(
                r"(\d{2,4})[/年.-](\d{1,2})[/月.-](\d{1,2})", date_val
            )
            if m_parsed_date:
              y_str, m_str, d_str = m_parsed_date.groups()
              yy = y_str[-2:]  # 年の下2桁
              mm = f"{int(m_str):02d}"  # 2桁の月
              dd = f"{int(d_str):02d}"  # 2桁の日
              auto_mgt_no = f"{yy}9{mm}{dd}"
            else:
              # 日付が万が一取れなかった場合のフォールバック（本日日付）
              now = datetime.now()
              auto_mgt_no = f"{now.strftime('%y')}9{now.strftime('%m%d')}"

            extracted_rows.append({
                "販売管理No": auto_mgt_no,
                "日付": date_val,
                "注文番号": order_no,
                "品名": item_text if item_text else "（要確認）",
                "数量": qty_text,
                "単価": price_text,
                "レコードID": "",
                "OCR区分": "要確認",
            })

          df = pd.DataFrame(extracted_rows)

          st.success("データ抽出が完了しました！（伝票日付連動型の販売管理No適用）")
          st.dataframe(df)

          csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
          st.download_button(
              label="📥 抽出データをCSVでダウンロード",
              data=csv_bytes,
              file_name="invoice_date_linked_extracted_data.csv",
              mime="text/csv",
          )