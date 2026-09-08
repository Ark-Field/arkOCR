import fitz  # PyMuPDF
from PIL import Image
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
    "日常の事務作業を効率化するための自分専用Webアプリ（OCR ＆"
    " カスタムトリミング・ガッチャンコ）"
)

# --- タブメニューの作成 ---
tab1, tab2 = st.tabs([
    "📄 OCR文字起こし (画像・PDF・表対応)",
    "✂️ カスタムトリミング＆ガッチャンコ",
])

# ==========================================
# タブ1：OCR文字起こし（画像 ＆ PDF ＆ 表対応）
# ==========================================
with tab1:
  st.header("📄 OCR文字起こし（画像 ＆ PDF）")
  st.write(
      "画像ファイル、またはPDFファイルをアップロードして文字を読み取ります。"
      "表形式の書類は「読み取りモード」を切り替えると精度が上がります。"
  )

  # --- 初めてのユーザー向けヘルプ・リンク ---
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

    # 表やレイアウトの精度を上げるための設定選択
    st.write("---")
    ocr_mode = st.selectbox(
        "📊 読み取りモード（表やレイアウトに合わせて調整）",
        [
            "標準 (Auto)",
            "表・ブロック優先 (PSM 6) ※表組みにおすすめ",
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

    # 1. 画像の場合
    if file_extension in ["png", "jpg", "jpeg"]:
      image = Image.open(uploaded_file)
      st.image(image, caption="アップロードされた画像", use_column_width=True)

      if st.button("画像から文字を読み取る", key="btn_img"):
        with st.spinner("画像から文字を解析中..."):
          img_gray = image.convert("L")
          text = pytesseract.image_to_string(
              img_gray, lang="jpn", config=custom_config
          )
          st.subheader("📝 読み取り結果")
          st.text_area("抽出されたテキスト", text, height=300)

    # 2. PDFの場合
    elif file_extension == "pdf":
      st.info("PDFファイルがアップロードされました。全ページの文字を読み取ります。")

      if st.button("PDFの文字を読み取る", key="btn_pdf"):
        with st.spinner("PDFを解析中... (表のレイアウトを調整中)"):
          uploaded_file.seek(0)
          doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
          all_text = ""

          for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            img_gray = img.convert("L")

            page_text = pytesseract.image_to_string(
                img_gray, lang="jpn", config=custom_config
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
  st.write(
      "2つのPDFの「必要な部分（上から・下からの％）」を指定して切り抜き、"
      "1枚のA4用紙に上下でまとめます。"
  )

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
          pix = page.get_pixmap(dpi=300)
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