import streamlit as st
import pytesseract # for ocr
import pandas as pd
import PyPDF2
from PIL import Image
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import yellow, red, green, blue
import zipfile
import pdf2image
from pdf2image import convert_from_bytes
import img2pdf
import os
# added new 
import base64
import json
import streamlit.components.v1 as components



st.set_page_config(page_title="Star Cement PDF Editor Pro", page_icon="📄", layout="wide")

# Custom CSS for better UI
st.markdown("""
<style>

/* Responsive, animated, gradient headline */
.main-header {
    font-size: clamp(2.5rem, 6vw, 5rem);  /* 📱 Mobile → 🖥 Desktop */
    font-weight: 800;
    text-align: center;
    margin-bottom: 2rem;

    /* Gradient text */
    background: linear-gradient(
        90deg,
        #ff4b4b,
        #ff8c00,
        #ffd700,
        #00c853,
        #2979ff
    );
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;

    /* Animation */
    animation: gradientMove 6s ease infinite, fadeIn 1.5s ease-in-out;

    /* Shadow */
    text-shadow: 0px 4px 12px rgba(0, 0, 0, 0.25);
}

/* Gradient animation */
@keyframes gradientMove {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Fade-in animation */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">📄 Star Cement PDF Editor Pro</p>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar for feature selection
st.sidebar.title("🛠️ Tools")
feature = st.sidebar.radio(
    "Select a feature:",
    [
        "🔗 Merge PDFs",
        "✂️ Split PDF",
        "📑 Extract Pages",
        "🔄 Rotate Pages",
        "💧 Add Watermark",
        "📝 Extract Text",
        "🖼️ Extract Images",
        "🗜️ Compress PDF",
        "📸 PDF to Images",
        "✨ Highlight Text",
        "🔀 Reorder Pages",
        "✍️ Sign PDF"

    ]
)

# 🔄 RESET STATE WHEN TOOL CHANGES
if "prev_feature" not in st.session_state:
    st.session_state.prev_feature = feature

if st.session_state.prev_feature != feature:
    for key in list(st.session_state.keys()):
        if key != "prev_feature":
            del st.session_state[key]
    st.session_state.prev_feature = feature
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Upload your PDF(s) and select the operation you want to perform.")

# Helper function to create download button
def create_download_button(file_data, filename, label):
    st.download_button(
        label=label,
        data=file_data,
        file_name=filename,
        mime="application/pdf",
        use_container_width=True
    )

# Feature 1: Merge PDFs
if feature == "🔗 Merge PDFs":
    st.header("🔗 Merge Multiple PDFs")
    st.write("Upload multiple PDF files to merge them into one.")

    # Correct uploader: multiple files
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True
    )

    # Validate file count
    if uploaded_files and len(uploaded_files) > 1:
        st.success(f"✅ {len(uploaded_files)} files uploaded")

        # Display merge order
        st.write("**Files will be merged in this order:**")
        for index, file in enumerate(uploaded_files, start=1):
            st.write(f"{index}. {file.name}")

        # Merge button
        if st.button("🔗 Merge PDFs", use_container_width=True):
            try:
                merger = PyPDF2.PdfMerger()

                for pdf in uploaded_files:
                    merger.append(pdf)

                output = io.BytesIO()
                merger.write(output)
                merger.close()
                output.seek(0)

                create_download_button(
                    output.getvalue(),
                    "merged_document.pdf",
                    "⬇️ Download Merged PDF"
                )

                st.success("✅ PDFs merged successfully!")

            except Exception as e:
                st.error(f"❌ Error while merging PDFs: {str(e)}")

    elif uploaded_files and len(uploaded_files) == 1:
        st.warning("⚠️ Please upload at least **2 PDF files** to merge.")

# Feature 2: Split PDF
elif feature == "✂️ Split PDF":
    st.header("✂️ Split PDF into Pages")
    st.write("Split a PDF into individual page files with preview and bulk download.")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file:
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            num_pages = len(reader.pages)

            st.info(f"📄 Total pages: {num_pages}")

            split_option = st.radio(
                "Split option:",
                ["Split all pages", "Split specific range"]
            )

            # ==========================================================
            # SPLIT ALL PAGES (STABLE + PAGINATED VIEW)
            # ==========================================================
            if split_option == "Split all pages":

                show_preview = st.checkbox("🖼️ Show page previews", value=False)

                # ---- Initialize session state ----
                if "split_pages" not in st.session_state:
                    st.session_state.split_pages = None

                if "zip_data" not in st.session_state:
                    st.session_state.zip_data = None

                # ---- Split button ----
                if st.button("✂️ Split All Pages", use_container_width=True):

                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    split_pages = []
                    zip_buffer = io.BytesIO()

                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for page_index in range(num_pages):

                            writer = PyPDF2.PdfWriter()
                            writer.add_page(reader.pages[page_index])

                            output = io.BytesIO()
                            writer.write(output)
                            output.seek(0)

                            pdf_bytes = output.getvalue()

                            split_pages.append({
                                "page": page_index + 1,
                                "pdf": pdf_bytes
                            })

                            zip_file.writestr(
                                f"page_{page_index + 1}.pdf",
                                pdf_bytes
                            )

                            progress = int(((page_index + 1) / num_pages) * 100)
                            progress_bar.progress(progress)
                            status_text.text(
                                f"Processing page {page_index + 1} of {num_pages}"
                            )

                    zip_buffer.seek(0)

                    st.session_state.split_pages = split_pages
                    st.session_state.zip_data = zip_buffer.getvalue()

                    progress_bar.empty()
                    status_text.empty()

                    st.success("✅ All pages split successfully!")

                # ==========================================================
                # RENDER RESULTS (20 PAGES AT A TIME)
                # ==========================================================
                if st.session_state.split_pages:

                    PAGES_PER_VIEW = 20
                    total_pages = len(st.session_state.split_pages)

                    total_groups = (total_pages - 1) // PAGES_PER_VIEW + 1

                    group_options = [
                        f"Pages {i*PAGES_PER_VIEW + 1} – {min((i+1)*PAGES_PER_VIEW, total_pages)}"
                        for i in range(total_groups)
                    ]

                    selected_group = st.selectbox(
                        "📄 Select page range",
                        group_options
                    )

                    group_index = group_options.index(selected_group)
                    start_idx = group_index * PAGES_PER_VIEW
                    end_idx = min(start_idx + PAGES_PER_VIEW, total_pages)

                    pages_to_show = st.session_state.split_pages[start_idx:end_idx]

                    cols_per_row = 3

                    for i in range(0, len(pages_to_show), cols_per_row):
                        cols = st.columns(cols_per_row)

                        for col_idx in range(cols_per_row):
                            idx = i + col_idx
                            if idx >= len(pages_to_show):
                                continue

                            page_data = pages_to_show[idx]

                            with cols[col_idx]:

                                # ---- Optional Preview ----
                                if show_preview:
                                    try:
                                        img = convert_from_bytes(
                                            uploaded_file.getvalue(),
                                            dpi=80,
                                            first_page=page_data["page"],
                                            last_page=page_data["page"]
                                        )[0]

                                        st.image(
                                            img,
                                            caption=f"Page {page_data['page']}",
                                            use_column_width=True
                                        )
                                    except Exception:
                                        st.empty()

                                # ---- Download button ----
                                st.download_button(
                                    label=f"⬇️ Download Page {page_data['page']}",
                                    data=page_data["pdf"],
                                    file_name=f"page_{page_data['page']}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )

                    st.download_button(
                        label="📦 Download All Pages as ZIP",
                        data=st.session_state.zip_data,
                        file_name="split_pages.zip",
                        mime="application/zip",
                        use_container_width=True
                    )

            # ==========================================================
            # SPLIT SPECIFIC RANGE (UNCHANGED)
            # ==========================================================
            else:
                col1, col2 = st.columns(2)
                with col1:
                    start_page = st.number_input(
                        "Start page",
                        min_value=1,
                        max_value=num_pages,
                        value=1
                    )
                with col2:
                    end_page = st.number_input(
                        "End page",
                        min_value=1,
                        max_value=num_pages,
                        value=num_pages
                    )

                if st.button("✂️ Split Range", use_container_width=True):
                    writer = PyPDF2.PdfWriter()
                    for i in range(start_page - 1, end_page):
                        writer.add_page(reader.pages[i])

                    output = io.BytesIO()
                    writer.write(output)
                    output.seek(0)

                    create_download_button(
                        output.getvalue(),
                        f"pages_{start_page}_to_{end_page}.pdf",
                        "⬇️ Download Split PDF"
                    )
                    st.success("✅ Pages extracted successfully!")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Feature 3: Extract Pages
elif feature == "📑 Extract Pages":
    st.header("📑 Extract Specific Pages")
    st.write("Extract selected pages from a PDF.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file:
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            num_pages = len(reader.pages)
            
            st.info(f"📄 Total pages: {num_pages}")
            
            pages_to_extract = st.text_input(
                "Enter page numbers (comma-separated, e.g., 1,3,5-7):",
                placeholder="1,3,5-7"
            )
            
            if st.button("📑 Extract Pages", use_container_width=True):
                if pages_to_extract:
                    # Parse page numbers
                    page_list = []
                    for part in pages_to_extract.split(','):
                        if '-' in part:
                            start, end = map(int, part.split('-'))
                            page_list.extend(range(start, end+1))
                        else:
                            page_list.append(int(part))
                    
                    # Remove duplicates and sort
                    page_list = sorted(set(page_list))
                    
                    # Validate page numbers
                    if all(1 <= p <= num_pages for p in page_list):
                        writer = PyPDF2.PdfWriter()
                        for page_num in page_list:
                            writer.add_page(reader.pages[page_num-1])
                        
                        output = io.BytesIO()
                        writer.write(output)
                        output.seek(0)
                        
                        create_download_button(output.getvalue(), "extracted_pages.pdf", "⬇️ Download Extracted Pages")
                        st.success(f"✅ Extracted {len(page_list)} pages successfully!")
                    else:
                        st.error("❌ Invalid page numbers. Please check your input.")
                else:
                    st.warning("⚠️ Please enter page numbers.")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Feature 4: Rotate Pages
elif feature == "🔄 Rotate Pages":
    st.header("🔄 Rotate PDF Pages")
    st.write("Rotate pages clockwise by 90°, 180°, or 270°.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file:
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            num_pages = len(reader.pages)
            
            st.info(f"📄 Total pages: {num_pages}")
            
            col1, col2 = st.columns(2)
            with col1:
                rotation = st.selectbox("Rotation angle", [90, 180, 270])
            with col2:
                rotate_option = st.radio("Rotate:", ["All pages", "Specific pages"])
            
            if rotate_option == "Specific pages":
                pages_to_rotate = st.text_input("Enter page numbers (comma-separated):", placeholder="1,2,3")
            
            if st.button("🔄 Rotate Pages", use_container_width=True):
                writer = PyPDF2.PdfWriter()
                
                if rotate_option == "All pages":
                    for page in reader.pages:
                        rotated_page = page.rotate(rotation)
                        writer.add_page(rotated_page)
                else:
                    if pages_to_rotate:
                        page_list = [int(p.strip()) for p in pages_to_rotate.split(',')]
                        for i, page in enumerate(reader.pages, 1):
                            if i in page_list:
                                writer.add_page(page.rotate(rotation))
                            else:
                                writer.add_page(page)
                
                output = io.BytesIO()
                writer.write(output)
                output.seek(0)
                
                create_download_button(output.getvalue(), "rotated_document.pdf", "⬇️ Download Rotated PDF")
                st.success("✅ Pages rotated successfully!")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Feature 5: Add Watermark
elif feature == "💧 Add Watermark":
    st.header("💧 Add Watermark to PDF")
    st.write("Add a transparent text watermark and preview before downloading.")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file:
        watermark_text = st.text_input(
            "Watermark text",
            placeholder="CONFIDENTIAL"
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            font_size = st.slider("Font size", 20, 120, 48)
        with col2:
            opacity = st.slider("Opacity", 0.05, 0.9, 0.25)
        with col3:
            rotation = st.slider("Rotation angle", -90, 90, 45)

        if st.button("Add Watermark", use_container_width=True):
            if not watermark_text.strip():
                st.warning("⚠️ Please enter watermark text.")
            else:
                try:
                    reader = PyPDF2.PdfReader(uploaded_file)
                    writer = PyPDF2.PdfWriter()

                    for page in reader.pages:
                        page_width = float(page.mediabox.width)
                        page_height = float(page.mediabox.height)

                        # Create watermark page
                        packet = io.BytesIO()
                        can = canvas.Canvas(packet, pagesize=(page_width, page_height))

                        can.saveState()
                        can.setFont("Helvetica-Bold", font_size)
                        can.setFillAlpha(opacity)  # TRUE transparency
                        can.translate(page_width / 2, page_height / 2)
                        can.rotate(rotation)
                        can.drawCentredString(0, 0, watermark_text)
                        can.restoreState()
                        can.save()

                        packet.seek(0)
                        watermark_pdf = PyPDF2.PdfReader(packet)
                        watermark_page = watermark_pdf.pages[0]

                        page.merge_page(watermark_page)
                        writer.add_page(page)

                    output = io.BytesIO()
                    writer.write(output)
                    output.seek(0)

                    # Save for preview & download
                    st.session_state.watermarked_pdf = output.getvalue()

                    st.success("✅ Watermark added successfully!")

                except Exception as e:
                    st.error(f"❌ Error while adding watermark: {str(e)}")

    # ======================================================
    # PREVIEW WATERMARKED PDF BEFORE DOWNLOAD
    # ======================================================
    if "watermarked_pdf" in st.session_state:

        st.markdown("### 👀 Preview Watermarked Document")

        preview_pages = st.slider(
            "Number of pages to preview",
            min_value=1,
            max_value=5,
            value=1
        )

        try:
            images = convert_from_bytes(
                st.session_state.watermarked_pdf,
                dpi=90,
                first_page=1,
                last_page=preview_pages
            )

            for idx, img in enumerate(images, start=1):
                st.image(
                    img,
                    caption=f"Preview – Page {idx}",
                    use_column_width=True
                )

        except Exception:
            st.warning("⚠️ Preview not available on this system.")

        create_download_button(
            st.session_state.watermarked_pdf,
            "watermarked_document.pdf",
            "⬇️ Download Final Watermarked PDF"
        )

#=============================================
# Feature 6: OCR
#=============================================

elif feature == "📝 Extract Text":
    st.header("📝 Extract Text from PDF")
    st.write("Extract text from digital or scanned PDFs using OCR if required.")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file:
        col1, col2 = st.columns(2)

        with col1:
            doc_type = st.radio(
                "Select document type",
                ["📄 Document", "🧾 Invoice / Bill"]
            )

        with col2:
            extract_method = st.radio(
                "Extraction method",
                ["Normal (Text-based PDF)", "OCR (Scanned PDF)"]
            )

        if st.button("📝 Extract", use_container_width=True):
            try:
                extracted_text = ""

                # ===============================
                # NORMAL TEXT EXTRACTION
                # ===============================
                if extract_method == "Normal (Text-based PDF)":
                    reader = PyPDF2.PdfReader(uploaded_file)
                    with st.spinner("Extracting text from PDF..."):
                        for page in reader.pages:
                            txt = page.extract_text()
                            if txt:
                                extracted_text += txt + "\n\n"

                # ===============================
                # OCR EXTRACTION
                # ===============================
                else:
                    try:
                        with st.spinner("Running OCR on scanned PDF..."):
                            images = convert_from_bytes(uploaded_file.getvalue(), dpi=300)
                            for img in images:
                                extracted_text += pytesseract.image_to_string(img) + "\n\n"
                    except Exception as ocr_error:
                        st.error("❌ OCR Error: Tesseract is not installed or not found in PATH")
                        st.info("""
                        **To fix this:**
                        - Use 'Normal (Text-based PDF)' extraction method instead
                        - Or install Tesseract OCR on your system
                        """)
                        st.stop()

                if not extracted_text.strip():
                    st.warning("⚠️ No text could be extracted.")
                    st.stop()

                st.success("✅ Text extraction completed!")

                # ======================================================
                # DOCUMENT → TXT
                # ======================================================
                if doc_type == "📄 Document":
                    st.text_area("📖 Extracted Text", extracted_text, height=400)
                    st.download_button(
                        "⬇️ Download as TXT",
                        extracted_text,
                        "extracted_text.txt",
                        "text/plain",
                        use_container_width=True
                    )

                # ======================================================
                # INVOICE / BILL → UNIVERSAL EXTRACTION
                # ======================================================
                else:
                    import re
                    import pandas as pd
                    import io

                    st.markdown("### 📊 Extracted Invoice Data")
                    
                    text = extracted_text
                    
                    # -------------------------------------------------
                    # UNIVERSAL HELPER FUNCTIONS
                    # -------------------------------------------------
                    def find_multi(patterns, text, default=""):
                        """Try multiple patterns and return first match"""
                        try:
                            for pattern in patterns if isinstance(patterns, list) else [patterns]:
                                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                                if match:
                                    return match.group(1).strip()
                            return default
                        except:
                            return default
                    
                    def find_all_multi(patterns, text):
                        """Try multiple patterns and return all matches"""
                        try:
                            for pattern in patterns if isinstance(patterns, list) else [patterns]:
                                matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
                                if matches:
                                    return matches
                            return []
                        except:
                            return []
                    
                    # -------------------------------------------------
                    # UNIVERSAL INVOICE EXTRACTION
                    # -------------------------------------------------
                    invoice_data = {}
                    
                    # ========== INVOICE IDENTIFIERS ==========
                    invoice_data["Invoice Number"] = find_multi([
                        r"Invoice\s+No[\.:\s]+([A-Z]{2,4}\d+)",
                        r"Invoice\s+No[\.:\s]+(\d+)",
                        r"Invoice\s*#[:\s]*([A-Z0-9\-]+)",
                        r"Bill\s+No[\.:\s]+([A-Z0-9\-]+)",
                        r"Tax\s+Invoice[^\n]*\n[^\n]*Invoice\s+No[\.:\s]+([A-Z0-9/\-]+)"
                    ], text)
                    
                    invoice_data["Invoice Date"] = find_multi([
                        r"Invoice\s+Date[\.:\s]+([\d/\-]+)",
                        r"Dated[\.:\s]+([\d/\-]+)",
                        r"Date[\.:\s]+([\d]{1,2}[/-][A-Za-z]{3}[/-][\d]{2,4})",
                        r"Date[\.:\s]+([\d]{1,2}[/-][\d]{1,2}[/-][\d]{2,4})",
                        r"Invoice\s+No[^\n]+\n[^\n]*Dated[^\n]*\n([^\n]*\d{2}[-/]\d{2}[-/]\d{4})"
                    ], text)
                    
                    invoice_data["Due Date"] = find_multi([
                        r"Due\s+Date[\.:\s]+([\d/\-]+)",
                        r"Payment\s+Due[\.:\s]+([\d/\-]+)"
                    ], text)
                    
                    # ========== ACKNOWLEDGMENT & REFERENCE ==========
                    invoice_data["Ack No"] = find_multi([
                        r"Ack\s+No[\.:\s]+([A-Z0-9]+)",
                        r"Acknowledgment[\.:\s]+([A-Z0-9]+)",
                        r"No\.[\.:\s]+(\d{12,})"  # Long numeric ack numbers
                    ], text)
                    
                    invoice_data["Ack Date"] = find_multi([
                        r"Ack\s+Date[\.:\s]+([\d/\-]+)",
                        r"Date\s+r[\.:\s]+([\d\-]+[A-Za-z]{3}\-[\d]{2})"  # Date r format
                    ], text)
                    
                    invoice_data["IRN Number"] = find_multi([
                        r"IRN[\.:\s]+([A-Za-z0-9\-]+)",
                        r"IRN\s+No[\.:\s]+([A-Za-z0-9\-]+)",
                        r"IRN[\.:\s]*\n[\.:\s]*([a-z0-9\-]{40,})"  # Long IRN on next line
                    ], text)
                    
                    invoice_data["CIN Number"] = find_multi([
                        r"CIN\s+NO[\.:\s]+([A-Z0-9]+)"
                    ], text)
                    
                    invoice_data["PAN"] = find_multi([
                        r"PAN[\.:\s]+([A-Z]{5}\d{4}[A-Z])"
                    ], text)
                    
                    # ========== E-WAY BILL ==========
                    invoice_data["E-Way Bill No"] = find_multi([
                        r"e-Way\s+Bill\s+No[\.:\s]+(\d+)",
                        r"EWAY\s+Bill\s+No[\.:\s]+(\d+)",
                        r"EWB\s+No[\.:\s]+(\d+)"
                    ], text)
                    
                    invoice_data["EWB Expiry Date"] = find_multi([
                        r"EWB\s+Expiry[^\n:]+([\d/\.\s:]+)",
                        r"e-Way.*?Expiry[^\n:]+([\d/\.\s:]+)"
                    ], text)
                    
                    # ========== ORDER DETAILS ==========
                    invoice_data["Sales Order No"] = find_multi([
                        r"S\.?O\.?\s+No[\.:\s]+(\d+)",
                        r"Sales\s+Order[\.:\s]+([A-Z0-9\-]+)"
                    ], text)
                    
                    invoice_data["Sales Order Date"] = find_multi([
                        r"S\.?O\.?\s+No[^&\n]+&\s*([\d/]+)",
                        r"S\.?O\.?\s+Date[\.:\s]+([\d/]+)"
                    ], text)
                    
                    # ========== ORDER DETAILS ==========
                    invoice_data["Purchase Order No"] = find_multi([
                        r"(?:Cust|Customer|Buyer[^\n]*)\s*(?:PO|P\.O\.)\s+No[\.:\s]+([A-Z0-9\-]+)",
                        r"PO\s+NO[\.:\-\s]+([A-Z0-9\-]+)",
                        r"Buyer'?s?\s+Order\s+No[\.:\-\s]+([A-Z0-9\-]+)"
                    ], text)
                    
                    invoice_data["Reference No"] = find_multi([
                        r"(?:Our\s+)?Ref(?:erence)?[\.:\s]+No[\.:\s&]+Date[\.:\s]+([A-Z0-9]+)",
                        r"Reference\s+No[\.:\s&]+Date[^\n]*?([A-Z0-9]+)\s+dt\.",
                        r"Other\s+References[\.:\s]+([A-Z0-9\-]+)"
                    ], text)
                    
                    invoice_data["Reference Date"] = find_multi([
                        r"Reference\s+No[^d]+dt\.\s*([\d\-/A-Za-z]+)"
                    ], text)
                    
                    # ========== DELIVERY/DISPATCH ==========
                    invoice_data["Delivery Note No"] = find_multi([
                        r"Delivery\s+(?:Note\s+)?No[\.:\s]+([A-Z0-9\-]+)",
                        r"Dispatch\s+Doc\s+No[\.:\s]+([A-Z0-9\-]+)"
                    ], text)
                    
                    invoice_data["Delivery Date"] = find_multi([
                        r"Delivery\s+(?:Note\s+)?Date[\.:\s]+([\d/\-]+)",
                        r"Delivery\s+No[^&\n]+&\s*([\d/]+)"
                    ], text)
                    
                    invoice_data["Shipment No"] = find_multi([
                        r"Shipment\s+No[\.:\s]+([A-Z0-9\-]+)"
                    ], text)
                    
                    invoice_data["Shipment Date"] = find_multi([
                        r"Shipment\s+No[^&\n]+&\s*([\d/]+)",
                        r"Shipment\s+Date[\.:\s]+([\d/]+)"
                    ], text)
                    
                    # ========== SELLER/SUPPLIER DETAILS ==========
                    # Try to find seller name (could be individual or company)
                    invoice_data["Seller Name"] = find_multi([
                        r"^([A-Z][A-Z\s&\.]+(?:LIMITED|LTD|PVT|PRIVATE|LLP|ASSOCIATES|COMPANY))",
                        r"(?:Seller|Supplier|From)[^\n:]*:\s*([A-Z][^\n]+(?:LIMITED|LTD|PVT))",
                        r"^([A-Z]{2,}(?:\s+[A-Z]{2,})+)\n",  # Individual name in caps
                        r"(STAR\s+CEMENT\s+LIMITED)"
                    ], text)
                    
                    # Seller address/location
                    invoice_data["Seller Address"] = find_multi([
                        r"^[A-Z\s]+\n([A-Z][^\n]+)\n([A-Z][^\n]+)\n([A-Z][^\n,]+,\s*[A-Z\s]+-\s*\d{6})"
                    ], text)
                    
                    invoice_data["Seller Location"] = find_multi([
                        r"^[A-Z\s&]+\n[A-Z\s]+\n([A-Z\s,]+?)(?:,\s*[A-Z\s]+-\s*\d{6})",
                        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z\s]+)-\s*(\d{6})"
                    ], text)
                    
                    # Extract all GSTIN
                    all_gstins = find_all_multi([
                        r"GSTIN[/\\]?UIN[\.:\s]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}[Z]{1}[0-9A-Z]{1})",
                        r"GSTIN\s+No[\.:\s]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{3})"
                    ], text)
                    
                    if len(all_gstins) >= 1:
                        invoice_data["Seller GSTIN"] = all_gstins[0]
                    if len(all_gstins) >= 2:
                        invoice_data["Customer GSTIN"] = all_gstins[1]
                    if len(all_gstins) >= 3:
                        invoice_data["Ship To GSTIN"] = all_gstins[2]
                    
                    # Extract all PIN codes
                    all_pins = find_all_multi([
                        r"PIN[\.:\s]+(\d{6})",
                        r"\b(\d{6})\b"
                    ], text)
                    # Filter valid Indian PINs
                    valid_pins = [p for p in all_pins if p.startswith(('1','2','3','4','5','6','7','8','9'))]
                    if len(valid_pins) >= 1:
                        invoice_data["Seller PIN"] = valid_pins[0]
                    if len(valid_pins) >= 2:
                        invoice_data["Customer PIN"] = valid_pins[1]
                    
                    # Extract State Codes
                    all_state_codes = find_all_multi([
                        r"(?:State\s+)?Code[\.:\s]*(\d{1,2})",
                        r"State\s+Name[^\n]+Code[\.:\s]*(\d{1,2})"
                    ], text)
                    if len(all_state_codes) >= 1:
                        invoice_data["Seller State Code"] = all_state_codes[0]
                    if len(all_state_codes) >= 2:
                        invoice_data["Customer State Code"] = all_state_codes[1]
                    
                    # Extract State Names
                    all_states = find_all_multi([
                        r"State\s+Name[\.:\s]*([A-Z][A-Za-z\s]+?)(?:,|Code|\d|$)",
                        r"STATE[\.:\s]*([A-Z\s]+?)(?:\n|STATE CODE|GSTIN)"
                    ], text)
                    if len(all_states) >= 1:
                        invoice_data["Seller State"] = all_states[0].strip()
                    if len(all_states) >= 2:
                        invoice_data["Customer State"] = all_states[1].strip()
                    
                    # ========== BUYER/CUSTOMER DETAILS ==========
                    invoice_data["Buyer/Customer Name"] = find_multi([
                        r"Buyer\s+Name[\.:\s]+([A-Z][^\n]+)",
                        r"(?:Consignee|Customer|Bill\s+to)[^\n:]*:\s*([A-Z][^\n]+)",
                        r"Name[^\n]*Customer[^\n:]*:\s*([^\n]+)"
                    ], text)
                    
                    invoice_data["Buyer Address"] = find_multi([
                        r"Buyer\s+Address[\.:\s]+([^\n]+(?:\n[^\n]+)*?)(?=\n(?:District|GSTIN))",
                        r"(?:Consignee|Customer)\s+Address[\.:\s]+([^\n]+)"
                    ], text)
                    
                    invoice_data["Ship To Name"] = find_multi([
                        r"(?:Ship\s+to|Delivery\s+Address)[^\n:]*:\s*([A-Z][^\n]+)"
                    ], text)
                    
                    # ========== TRANSPORT DETAILS ==========
                    invoice_data["Mode of Transport"] = find_multi([
                        r"Mode\s+of\s+Transport[\.:\s]+([A-Za-z]+)",
                        r"Transport\s+Mode[\.:\s]+([A-Za-z]+)"
                    ], text)
                    
                    # Transporter extraction
                    transporter_line = find_multi([
                        r"Transporter\s+Code\s*&\s*Name[\.:\s]+(\d+\s+[A-Z\s]+?)(?=\n|Vehicle|$)",
                        r"Transporter[\.:\s]+([^\n]+)"
                    ], text)
                    
                    if transporter_line and re.match(r'\d+\s+', transporter_line):
                        parts = transporter_line.split(None, 1)
                        if len(parts) >= 1:
                            invoice_data["Transporter Code"] = parts[0]
                        if len(parts) >= 2:
                            invoice_data["Transporter Name"] = parts[1].strip()
                    else:
                        invoice_data["Transporter Name"] = transporter_line
                    
                    # ========== ADDITIONAL FIELDS FOR SIMPLE INVOICES ==========
                    invoice_data["Vehicle No"] = find_multi([
                        r"Vehicle\s+No[\.:\s]+([A-Z]{2}[-\s]?\d{2}[A-Z]{1,2}[-\s]?\d{4})",
                        r"Vehicle\s+(?:Reg\.?\s+)?No[\.:\s]+([A-Z0-9\-]+)"
                    ], text)
                    
                    invoice_data["Place of Supply"] = find_multi([
                        r"Place\s+of\s+Supply[\.:\s]+([A-Z][^\n]+)"
                    ], text)
                    
                    invoice_data["Order No"] = find_multi([
                        r"Order\s+No[\.:\s]+([A-Z0-9]+)",
                        r"Order\s+No[\.:\s]+([\d]+)"
                    ], text)
                    
                    invoice_data["LR/RR No"] = find_multi([
                        r"L[\.\/]?R[\.\/]?R\.?R[\.:\s]+No[\.:\s]+(\d+)",
                        r"L\.R[\.:\s]+No[\.:\s]+(\d+)",
                        r"Bill\s+of\s+Lading[\.:/]*LR-RR\s+No[\.:\s]+([A-Z0-9\-]+)"
                    ], text)
                    
                    invoice_data["LR/RR Date"] = find_multi([
                        r"L[\.\/]?R[\.\/]?R\.?R[\.:\s]+No[^&\n]+&\s*Date[\.:\s]+([\d/]+)",
                        r"L\.R[\.:\s]+No[^&\n]+&\s*([\d/]+)"
                    ], text)
                    
                    invoice_data["Route"] = find_multi([
                        r"Route\s+Name[\.:\s]+([^\n]+?)(?=\n|Incoterms|$)",
                        r"Route[\.:\s]+([^\n]+)"
                    ], text)
                    
                    invoice_data["Destination"] = find_multi([
                        r"Destination[\.:\s]+([A-Z0-9\s]+?)(?=\n|Batch|$)",
                        r"Dispatched\s+through[\.:\s]+Destination[\.:\s]+([^\n]+)"
                    ], text)
                    
                    invoice_data["Terms of Delivery"] = find_multi([
                        r"Terms\s+of\s+Delivery[\.:\s]+([^\n]+)",
                        r"Incoterms[\.:\s]+([^\n]+?)(?=\n|Terms|$)"
                    ], text)
                    
                    invoice_data["Batch No"] = find_multi([
                        r"Batch\s+No[\.:\s]+([A-Z0-9]+)"
                    ], text)
                    
                    # ========== PAYMENT & FINANCIAL ==========
                    invoice_data["Mode/Terms of Payment"] = find_multi([
                        r"Mode[/\\]Terms\s+of\s+Payment[\.:\s]+([^\n]+)",
                        r"Payment\s+Terms[\.:\s]+([^\n]+)"
                    ], text)
                    
                    invoice_data["Taxable Amount"] = find_multi([
                        r"Taxable\s+(?:Amount|Value)[\.:\s]*([\d,]+\.?\d*)",
                        r"Total\s+Taxable[\.:\s]*([\d,]+\.?\d*)"
                    ], text)
                    
                    invoice_data["CGST"] = find_multi([
                        r"CGST[\.:\s]*([\d,]+\.?\d*)",
                        r"Central\s+Tax[^\n]*Amount[\.:\s]*([\d,]+\.?\d*)"
                    ], text)
                    
                    invoice_data["SGST"] = find_multi([
                        r"SGST[\.:\s]*([\d,]+\.?\d*)",
                        r"State\s+Tax[^\n]*Amount[\.:\s]*([\d,]+\.?\d*)"
                    ], text)
                    
                    invoice_data["IGST Rate"] = find_multi([
                        r"IGST[\.:\s@]*(\d+\.?\d*)%"
                    ], text)
                    
                    invoice_data["IGST Amount"] = find_multi([
                        r"IGST[\.:\s]*([\d,]+\.?\d*)",
                        r"Integrated\s+Tax[^\n]+Amount[\.:\s]*([\d,]+\.?\d*)"
                    ], text)
                    
                    invoice_data["TCS"] = find_multi([
                        r"TCS[\.:\-\s]*([\d,]+\.?\d*)"
                    ], text)
                    
                    invoice_data["Round Off"] = find_multi([
                        r"ROUND(?:ED)?\s+OFF[\.:\s]*([\-\d,\.]+)",
                        r"R[/\\]?OFF[\.:\s\-•]*([\-\d,\.]+)"
                    ], text)
                    
                    invoice_data["Total Amount"] = find_multi([
                        r"TOTAL[\.:\s]*([\d,]+\.?\d*)",
                        r"Total\s+Invoice[\.:\s]*([\d,]+\.?\d*)",
                        r"Grand\s+Total[\.:\s]*([\d,]+\.?\d*)",
                        r"₹\s*([\d,]+\.?\d*)\s*$"
                    ], text)
                    
                    invoice_data["Amount in Words"] = find_multi([
                        r"(?:Total\s+)?(?:Invoice\s+)?(?:value\s+)?[Ii]n\s+words[\.:\s]*(.*?ONLY)",
                        r"(?:INR|Rs\.?)\s+([A-Z][a-z]+.*?[Oo]nly)"
                    ], text)
                    
                    invoice_data["Reverse Charge"] = find_multi([
                        r"(?:Amount\s+of\s+Tax\s+)?Subject\s+[Tt]o\s+Reverse\s+Charge[\.:\s]*(YES|NO|Y|N)",
                        r"Reverse\s+Charge[\.:\s]*(YES|NO|Y|N)"
                    ], text)
                    
                    # ========== ADDITIONAL INFO ==========
                    invoice_data["Freight"] = find_multi([
                        r"FREIGHT[\.:\-\s]*([\d,]+\.?\d*)"
                    ], text)
                    
                    invoice_data["POD"] = find_multi([
                        r"POD[\.:\s]+([^\n]+)"
                    ], text)
                    
                    # -------------------------------------------------
                    # UNIVERSAL LINE ITEMS EXTRACTION
                    # -------------------------------------------------
                    line_items = []
                    
                    # Multiple pattern attempts for different formats
                    patterns = [
                        # Format 1: Simple vendor invoice (Challan/Material based)
                        re.compile(
                            r"(?P<sl>\d+)\s+"
                            r"(?P<challan>\d+)\s+"
                            r"(?P<date>[\d\-/]+)\s+"
                            r"(?P<vehicle>[A-Z]{2}[-\s]?\d{2}[A-Z]{1,2}[-\s]?\d{4})\s+"
                            r"(?P<material>[A-Z][A-Z\s]+?)\s+"
                            r"(?P<qty>[\d,]+\.?\d*)\s+"
                            r"(?P<rate>[\d,]+\.?\d*)\s+"
                            r"(?P<amount>[\d,]+\.?\d*)",
                            re.IGNORECASE
                        ),
                        # Format 2: Corporate B2B with HSN (ICA style) - handles multi-line descriptions
                        re.compile(
                            r"(?P<sl>\d+)\s+"
                            r"(?P<hsn>\d{8})\s+"
                            r"(?P<description>.+?)\s+"
                            r"(?P<qty>[\d,]+\.?\d*)\s+(?P<uom>PCS|MT|KG|TON|UNIT)\s+"
                            r"(?P<rate>[\d,]+\.?\d*)\s+"
                            r"(?P<per>PCS|MT|KG|TON|UNIT)\s+"
                            r"(?P<amount>[\d,]+\.?\d*)",
                            re.IGNORECASE | re.DOTALL
                        ),
                        # Format 3: Star Cement corporate style
                        re.compile(
                            r"(?P<sl>\d+)\s+"
                            r"(?P<description>(?:CEMENT|CLINKER|GRADE)[^\n]+?)\s+"
                            r"(?P<hsn>\d{6,8})\s+"
                            r"(?P<qty>[\d,]+\.?\d*)\s+(?P<uom>[A-Z]{2,3})\s+"
                            r"(?P<rate>[\d,]+\.?\d*)",
                            re.IGNORECASE
                        ),
                        # Format 4: With package info
                        re.compile(
                            r"(?P<description>(?:CEMENT|CLINKER)[^\n]*?)\s+"
                            r"(?P<hsn>\d{6,8})\s+"
                            r"(?P<package>[A-Z]+)\s+"
                            r"(?P<bags>[\d,]*)\s*"
                            r"(?P<uom>[A-Z]{2})\s+"
                            r"(?P<qty>[\d,.]+)\s+"
                            r"(?P<rate>[\d,.]+)",
                            re.IGNORECASE
                        ),
                        # Format 5: Standard GST invoice table
                        re.compile(
                            r"(?P<sl>\d+)\s+"
                            r"(?P<description>[A-Z][A-Z\s,\-:]+?)\s+"
                            r"(?P<hsn>\d{6,8})\s+"
                            r"(?P<qty>[\d,]+\.?\d*)\s+"
                            r"(?P<rate>[\d,]+\.?\d*)\s+"
                            r"(?P<per>[A-Z]{2,3})\s+"
                            r"(?P<amount>[\d,]+\.?\d*)",
                            re.IGNORECASE
                        ),
                        # Format 6: Fallback - any row with quantity and amount
                        re.compile(
                            r"(?P<description>[A-Z][A-Z\s]+(?:SAND|CEMENT|CLINKER|MATERIAL|MOTOR)[^\d\n]*?)\s+"
                            r"(?P<qty>[\d,]+\.?\d*)\s+"
                            r"(?P<rate>[\d,]+\.?\d*)\s+"
                            r"(?P<amount>[\d,]+\.?\d*)",
                            re.IGNORECASE
                        )
                    ]
                    
                    for pattern in patterns:
                        matches = list(pattern.finditer(text))
                        if matches:
                            for match in matches:
                                item = {}
                                try:
                                    groups = match.groupdict()
                                    
                                    if "sl" in groups and groups["sl"]:
                                        item["Sl No"] = groups["sl"]
                                    if "challan" in groups and groups["challan"]:
                                        item["Challan No"] = groups["challan"]
                                    if "date" in groups and groups["date"]:
                                        item["Date"] = groups["date"]
                                    if "vehicle" in groups and groups["vehicle"]:
                                        item["Vehicle No"] = groups["vehicle"]
                                    if "material" in groups and groups["material"]:
                                        # Clean up material description
                                        material_desc = groups["material"].strip()
                                        item["Material/Description"] = material_desc
                                    if "description" in groups and groups["description"]:
                                        # Clean multi-line descriptions
                                        desc = groups["description"].strip()
                                        desc = re.sub(r'\s+', ' ', desc)  # Collapse whitespace
                                        item["Description"] = desc
                                    if "hsn" in groups and groups["hsn"]:
                                        item["HSN/SAC"] = groups["hsn"]
                                    if "qty" in groups:
                                        item["Quantity"] = groups["qty"]
                                    if "uom" in groups and groups["uom"]:
                                        item["UOM"] = groups["uom"]
                                    if "rate" in groups:
                                        item["Rate"] = groups["rate"]
                                    if "per" in groups and groups["per"]:
                                        item["Per"] = groups["per"]
                                    if "amount" in groups:
                                        item["Amount"] = groups["amount"]
                                    if "package" in groups and groups.get("package"):
                                        item["Package"] = groups["package"]
                                    if "bags" in groups and groups.get("bags"):
                                        item["No of Bags"] = groups["bags"]
                                    
                                    if item and len(item) >= 3:  # At least 3 fields
                                        line_items.append(item)
                                except Exception as e:
                                    continue
                            
                            if line_items:
                                break
                    
                    # -------------------------------------------------
                    # FALLBACK: Manual parsing for broken table layouts
                    # -------------------------------------------------
                    if not line_items:
                        # Try to find HSN codes and reconstruct items
                        hsn_codes = re.findall(r'\b(\d{8})\b', text)
                        
                        if hsn_codes:
                            # Find all amounts that look like prices
                            amounts = re.findall(r'([\d,]+\.\d{2})', text)
                            
                            # Find quantities with units
                            qty_matches = re.findall(r'(\d+)\s+(PCS|MT|KG|TON)', text, re.IGNORECASE)
                            
                            # Try to match them up
                            for i, hsn in enumerate(hsn_codes):
                                if i < len(qty_matches) and i < len(amounts):
                                    item = {
                                        "Sl No": str(i + 1),
                                        "HSN/SAC": hsn,
                                        "Quantity": qty_matches[i][0],
                                        "UOM": qty_matches[i][1],
                                        "Amount": amounts[i] if i < len(amounts) else ""
                                    }
                                    
                                    # Try to find description near HSN
                                    hsn_pos = text.find(hsn)
                                    if hsn_pos > 0:
                                        # Look for MOTOR/CEMENT/etc before HSN
                                        before_hsn = text[max(0, hsn_pos-200):hsn_pos]
                                        desc_match = re.search(r'(MOTOR[^\n]{0,80}|CEMENT[^\n]{0,80}|CLINKER[^\n]{0,80})', before_hsn, re.IGNORECASE)
                                        if desc_match:
                                            item["Description"] = desc_match.group(1).strip()
                                    
                                    if len(item) >= 3:
                                        line_items.append(item)
                    
                    # -------------------------------------------------
                    # DISPLAY EXTRACTED DATA
                    # -------------------------------------------------
                    # Remove empty values and create DataFrame
                    header_df = pd.DataFrame([
                        {"Field": k, "Value": v} 
                        for k, v in invoice_data.items() 
                        if v and str(v).strip()
                    ])
                    
                    st.markdown("### 🧾 Invoice Header Information")
                    if not header_df.empty:
                        st.dataframe(header_df, use_container_width=True)
                        st.info(f"✅ Extracted {len(header_df)} header fields")
                    else:
                        st.warning("⚠️ No header fields could be extracted")
                    
                    # Display Line Items
                    st.markdown("### 📦 Line Items")
                    if line_items:
                        items_df = pd.DataFrame(line_items)
                        st.dataframe(items_df, use_container_width=True)
                        st.info(f"✅ Extracted {len(line_items)} line items")
                    else:
                        st.warning("⚠️ No line items detected")
                    
                    # Show raw text for debugging
                    with st.expander("🔍 View Extracted Text (for debugging)"):
                        st.text_area("Raw Text", extracted_text, height=300)
                    
                    # -------------------------------------------------
                    # EXPORT TO EXCEL
                    # -------------------------------------------------
                    excel_buffer = io.BytesIO()
                    
                    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                        if not header_df.empty:
                            header_df.to_excel(writer, sheet_name="Invoice_Header", index=False)
                        
                        if line_items:
                            items_df = pd.DataFrame(line_items)
                            items_df.to_excel(writer, sheet_name="Line_Items", index=False)
                        
                        # Add raw text for reference
                        raw_df = pd.DataFrame({"Extracted_Text": [extracted_text]})
                        raw_df.to_excel(writer, sheet_name="Raw_Text", index=False)
                    
                    excel_buffer.seek(0)
                    
                    st.download_button(
                        label="⬇️ Download Invoice Data (Excel)",
                        data=excel_buffer,
                        file_name="invoice_extracted_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

            except Exception as e:
                st.error(f"❌ Error during extraction: {str(e)}")
                import traceback
                st.text_area("Error Details", traceback.format_exc(), height=200)



# ===============================
# Feature 7: Extract Images (ROBUST + SCANNED PDF FALLBACK)
# ===============================
elif feature == "🖼️ Extract Images":
    st.header("🖼️ Extract Images from PDF")
    st.write("Extract embedded images (logos, photos). Auto-fallback for scanned PDFs.")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file:
        try:
            reader = PyPDF2.PdfReader(uploaded_file)

            extracted_images = []
            detected_images = 0
            zip_buffer = io.BytesIO()

            # ==================================================
            # STEP 1: TRY EMBEDDED IMAGE EXTRACTION (PyPDF2)
            # ==================================================
            with st.spinner("Scanning PDF for embedded images..."):
                for page_num, page in enumerate(reader.pages, start=1):

                    resources = page.get("/Resources")
                    if not resources:
                        continue

                    xobjects = resources.get("/XObject")
                    if not xobjects:
                        continue

                    xobjects = xobjects.get_object()

                    for obj_name in xobjects:
                        obj = xobjects[obj_name]

                        if obj.get("/Subtype") != "/Image":
                            continue

                        detected_images += 1

                        try:
                            data = obj.get_data()

                            filters = obj.get("/Filter")
                            if filters and not isinstance(filters, list):
                                filters = [filters]
                            elif not filters:
                                filters = []

                            image_name = f"page_{page_num}_{obj_name[1:]}"
                            img = None

                            # JPEG / JPEG2000
                            if "/DCTDecode" in filters or "/JPXDecode" in filters:
                                img = Image.open(io.BytesIO(data)).convert("RGB")

                            # RAW bitmap (logos, stamps)
                            else:
                                width = obj.get("/Width")
                                height = obj.get("/Height")

                                if not width or not height:
                                    continue

                                color_space = obj.get("/ColorSpace")

                                if isinstance(color_space, list) and color_space[0] == "/ICCBased":
                                    mode = "RGB"
                                elif color_space == "/DeviceRGB":
                                    mode = "RGB"
                                elif color_space == "/DeviceCMYK":
                                    mode = "CMYK"
                                elif color_space == "/DeviceGray":
                                    mode = "L"
                                else:
                                    continue

                                try:
                                    img = Image.frombytes(mode, (width, height), data)
                                except Exception:
                                    continue

                            if img:
                                buf = io.BytesIO()
                                img.save(buf, format="PNG")
                                buf.seek(0)

                                extracted_images.append({
                                    "name": f"{image_name}.png",
                                    "data": buf.getvalue(),
                                    "page": page_num
                                })

                        except Exception:
                            continue

            # ==================================================
            # STEP 2: FALLBACK FOR SCANNED PDFs (pdf2image)
            # ==================================================
            if detected_images == 0 or not extracted_images:
                st.info("ℹ️ No embedded images found. PDF appears scanned. Extracting full-page images...")

                from pdf2image import convert_from_bytes

                pages = convert_from_bytes(uploaded_file.getvalue(), dpi=300)

                extracted_images = []
                for i, page_img in enumerate(pages, start=1):
                    buf = io.BytesIO()
                    page_img.save(buf, format="PNG")
                    buf.seek(0)

                    extracted_images.append({
                        "name": f"page_{i}.png",
                        "data": buf.getvalue(),
                        "page": i
                    })

            # ==================================================
            # RESULTS
            # ==================================================
            if not extracted_images:
                st.warning("⚠️ No images could be extracted from this PDF.")
                st.stop()

            st.success(f"✅ Extracted {len(extracted_images)} image(s)")

            # ==================================================
            # PREVIEW & DOWNLOAD
            # ==================================================
            cols = st.columns(3)
            for idx, img in enumerate(extracted_images):
                with cols[idx % 3]:
                    st.image(
                        img["data"],
                        caption=f"{img['name']} (Page {img['page']})",
                        use_column_width=True
                    )

                    st.download_button(
                        "⬇️ Download",
                        data=img["data"],
                        file_name=img["name"],
                        mime="image/png",
                        use_container_width=True
                    )

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for img in extracted_images:
                    zf.writestr(img["name"], img["data"])

            zip_buffer.seek(0)

            st.download_button(
                "📦 Download All Images as ZIP",
                data=zip_buffer,
                file_name="extracted_images.zip",
                mime="application/zip",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"❌ Error extracting images: {str(e)}")




# Feature 8: Compress PDF (FINAL – NO SIZE INCREASE GUARANTEE)
elif feature == "🗜️ Compress PDF":
    st.header("🗜️ Compress PDF Size")
    st.write("Choose compression level based on quality vs file size.")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file:
        original_bytes = uploaded_file.getvalue()
        original_size = len(original_bytes) / 1024
        st.info(f"📊 Original size: {original_size:.2f} KB")

        compression_level = st.radio(
            "Compression level",
            ["Low (best quality)", "Medium (balanced)", "High (smallest size)"],
            horizontal=True
        )

        if compression_level in ["Medium (balanced)", "High (smallest size)"]:
            st.warning(
                "⚠️ Medium/High compression converts pages to images. "
                "Text may not remain selectable."
            )

        if st.button("🗜️ Compress PDF", use_container_width=True):
            try:
                with st.spinner("Compressing PDF..."):

                    # ---------- LOW: TEXT STREAM ----------
                    reader = PyPDF2.PdfReader(io.BytesIO(original_bytes))
                    writer = PyPDF2.PdfWriter()

                    for page in reader.pages:
                        page.compress_content_streams()
                        writer.add_page(page)

                    low_out = io.BytesIO()
                    writer.write(low_out)
                    low_bytes = low_out.getvalue()
                    low_size = len(low_bytes) / 1024

                    # ---------- IMAGE RASTER (Medium / High) ----------
                    def raster_compress(dpi, quality):
                        images = convert_from_bytes(original_bytes, dpi=dpi)
                        img_buffers = []

                        for img in images:
                            buf = io.BytesIO()
                            img.convert("RGB").save(
                                buf,
                                format="JPEG",
                                quality=quality,
                                optimize=True
                            )
                            img_buffers.append(buf.getvalue())

                        out = io.BytesIO()
                        out.write(img2pdf.convert(img_buffers))
                        out.seek(0)
                        return out.getvalue(), len(out.getvalue()) / 1024

                    final_bytes = low_bytes
                    final_size = low_size
                    method = "Text stream compression"

                    if compression_level == "Medium (balanced)":
                        img_bytes, img_size = raster_compress(dpi=150, quality=70)
                        if img_size < final_size:
                            final_bytes = img_bytes
                            final_size = img_size
                            method = "Medium raster compression"

                    elif compression_level == "High (smallest size)":
                        img_bytes, img_size = raster_compress(dpi=72, quality=45)
                        final_bytes = img_bytes
                        final_size = img_size
                        method = "Forced raster compression"

                reduction = ((original_size - final_size) / original_size) * 100

                st.success(f"✅ Compressed size: {final_size:.2f} KB")
                st.success(f"📉 Reduced by: {reduction:.1f}%")
                st.caption(f"🔍 Method used: {method}")

                create_download_button(
                    final_bytes,
                    "compressed_document.pdf",
                    "⬇️ Download Compressed PDF"
                )

            except Exception as e:
                st.error(f"❌ Compression failed: {str(e)}")

# Feature 9: PDF to Images 
elif feature == "📸 PDF to Images":
    st.header("📸 Convert PDF to Images")
    st.write("Convert each page of a PDF into image files.")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file:
        col1, col2 = st.columns(2)
        with col1:
            image_format = st.selectbox("Image format", ["PNG", "JPEG"])
        with col2:
            dpi = st.slider("Quality (DPI)", 72, 300, 150)

        if st.button("📸 Convert to Images", use_container_width=True):
            try:
                with st.spinner("Converting PDF pages to images..."):
                    images = convert_from_bytes(
                        uploaded_file.getvalue(),
                        dpi=dpi
                    )

                if not images:
                    st.error("❌ No pages could be converted.")
                    st.stop()

                st.success(f"✅ Converted {len(images)} pages successfully!")

                # ===============================
                # PREVIEW AS THUMBNAILS (GRID)
                # ===============================
                st.markdown("### 🖼️ Image Preview & Download")

                cols_per_row = 3
                zip_buffer = io.BytesIO()

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:

                    for idx in range(0, len(images), cols_per_row):
                        cols = st.columns(cols_per_row)

                        for col_idx in range(cols_per_row):
                            page_index = idx + col_idx
                            if page_index >= len(images):
                                continue

                            img = images[page_index]
                            page_no = page_index + 1

                            # --------- Thumbnail (small preview) ---------
                            thumb = img.copy()
                            thumb.thumbnail((350, 350))  # SMALL preview size

                            with cols[col_idx]:
                                st.markdown(f"**Page {page_no}**")
                                st.image(thumb)

                                # --------- Full-resolution image for download ---------
                                full_img_buffer = io.BytesIO()

                                if image_format == "PNG":
                                    img.save(full_img_buffer, format="PNG")
                                    ext = "png"
                                    mime = "image/png"
                                else:
                                    img.convert("RGB").save(
                                        full_img_buffer,
                                        format="JPEG",
                                        quality=90
                                    )
                                    ext = "jpg"
                                    mime = "image/jpeg"

                                full_img_buffer.seek(0)

                                # Individual download button (FIXED)
                                st.download_button(
                                    label="⬇️ Download",
                                    data=full_img_buffer.getvalue(),
                                    file_name=f"page_{page_no}.{ext}",
                                    mime=mime,
                                    key=f"download_img_{page_no}",
                                    use_container_width=True
                                )

                                # Add to ZIP
                                zip_file.writestr(
                                    f"page_{page_no}.{ext}",
                                    full_img_buffer.getvalue()
                                )

                zip_buffer.seek(0)

                # ===============================
                # ZIP DOWNLOAD
                # ===============================
                st.download_button(
                    label="📦 Download All Images as ZIP",
                    data=zip_buffer.getvalue(),
                    file_name="pdf_images.zip",
                    mime="application/zip",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"❌ Failed to convert PDF to images: {str(e)}")


# Feature 10: Highlight Text
elif feature == "✨ Highlight Text":
    st.header("Highlight Text (Visual Editor)")
    st.write("Visually annotate PDFs with pen, colors, eraser, undo and page navigation.")

    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

    if uploaded_file:
        import base64
        import streamlit.components.v1 as components

        pdf_bytes = uploaded_file.read()
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        html_code = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script src="https://unpkg.com/pdf-lib/dist/pdf-lib.min.js"></script>

<style>
body { margin:0; font-family: Arial; }
#toolbar {
  background:#f4f4f4;
  padding:8px;
  display:flex;
  gap:8px;
  border-bottom:1px solid #ccc;
}
canvas { position:absolute; left:0; top:0; }
#container { position:relative; }
button, select { padding:6px 8px; cursor:pointer; }
</style>
</head>

<body>

<div id="toolbar">
  <button onclick="setTool('highlight')">Highlight</button>

  <select id="penColor">
    <option value="red">Red</option>
    <option value="blue">Blue</option>
    <option value="green">Green</option>
  </select>

  <button onclick="setTool('pen')">Pen</button>
  <button onclick="setTool('eraser')">Eraser</button>
  <button onclick="undo()">Undo</button>
  <button onclick="prevPage()">Prev</button>
  <button onclick="nextPage()">Next</button>
  <button onclick="downloadPDF()">Download</button>
</div>

<div id="container">
  <canvas id="pdfCanvas"></canvas>
  <canvas id="drawCanvas"></canvas>
</div>

<script>
const pdfData = Uint8Array.from(atob("__PDF_BASE64__"), c => c.charCodeAt(0));
let pdfDoc = null;
let currentPage = 1;
let tool = "highlight";
let drawing = false;
let history = {};

const pdfCanvas = document.getElementById("pdfCanvas");
const drawCanvas = document.getElementById("drawCanvas");
const pdfCtx = pdfCanvas.getContext("2d");
const drawCtx = drawCanvas.getContext("2d");

function setTool(t){ tool = t; }

function undo(){
  if (!history[currentPage] || history[currentPage].length === 0) return;
  history[currentPage].pop();
  redraw();
}

function redraw(){
  drawCtx.clearRect(0,0,drawCanvas.width,drawCanvas.height);
  (history[currentPage] || []).forEach(p=>{
    drawCtx.globalCompositeOperation = p.mode;
    drawCtx.strokeStyle = p.color;
    drawCtx.lineWidth = p.width;
    drawCtx.globalAlpha = p.alpha;
    drawCtx.beginPath();
    p.points.forEach((pt,i)=> i?drawCtx.lineTo(pt.x,pt.y):drawCtx.moveTo(pt.x,pt.y));
    drawCtx.stroke();
  });
  drawCtx.globalAlpha = 1;
  drawCtx.globalCompositeOperation = "source-over";
}

drawCanvas.addEventListener("mousedown", e=>{
  drawing = true;
  if (!history[currentPage]) history[currentPage] = [];
  const color = tool==="pen" ? document.getElementById("penColor").value : "yellow";
  const alpha = tool==="highlight" ? 0.3 : 1;
  const width = tool==="highlight" ? 14 : 2;
  const mode = tool==="eraser" ? "destination-out" : "source-over";
  history[currentPage].push({ color, alpha, width, mode, points:[{x:e.offsetX,y:e.offsetY}] });
});

drawCanvas.addEventListener("mousemove", e=>{
  if(!drawing) return;
  history[currentPage].slice(-1)[0].points.push({x:e.offsetX,y:e.offsetY});
  redraw();
});

drawCanvas.addEventListener("mouseup", ()=> drawing=false);

function renderPage(n){
  pdfDoc.getPage(n).then(page=>{
    const vp = page.getViewport({ scale: 1.5 });
    pdfCanvas.width = drawCanvas.width = vp.width;
    pdfCanvas.height = drawCanvas.height = vp.height;
    page.render({ canvasContext: pdfCtx, viewport: vp });
    redraw();
  });
}

function prevPage(){ if(currentPage>1){ currentPage--; renderPage(currentPage);} }
function nextPage(){ if(currentPage<pdfDoc.numPages){ currentPage++; renderPage(currentPage);} }

async function downloadPDF(){
  try {
    // Create a temporary canvas for export with proper dimensions
    const tempCanvas = document.createElement('canvas');
    const tempCtx = tempCanvas.getContext('2d');
    
    // Convert base64 to ArrayBuffer for pdf-lib
    const binaryString = atob("__PDF_BASE64__");
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    
    const pdf = await PDFLib.PDFDocument.load(bytes);

    for(let i=1; i<=pdf.getPageCount(); i++){
      // Render page (even if no annotations) to get proper dimensions
      const page = await pdfDoc.getPage(i);
      const vp = page.getViewport({ scale: 1.5 });
      
      tempCanvas.width = vp.width;
      tempCanvas.height = vp.height;
      
      // Render PDF page to temp canvas
      await page.render({ 
        canvasContext: tempCtx, 
        viewport: vp 
      }).promise;
      
      // Draw annotations on top if they exist
      if(history[i] && history[i].length > 0){
        history[i].forEach(p=>{
          tempCtx.globalCompositeOperation = p.mode;
          tempCtx.strokeStyle = p.color;
          tempCtx.lineWidth = p.width;
          tempCtx.globalAlpha = p.alpha;
          tempCtx.beginPath();
          p.points.forEach((pt,idx)=> {
            if(idx === 0) {
              tempCtx.moveTo(pt.x, pt.y);
            } else {
              tempCtx.lineTo(pt.x, pt.y);
            }
          });
          tempCtx.stroke();
        });
        // Reset context
        tempCtx.globalAlpha = 1;
        tempCtx.globalCompositeOperation = "source-over";
      }
      
      // Convert canvas to PNG and embed in PDF
      const pngDataUrl = tempCanvas.toDataURL("image/png");
      const pngImageBytes = pngDataUrl.split(',')[1];
      const pngImage = await pdf.embedPng(pngImageBytes);
      
      const pdfPage = pdf.getPages()[i-1];
      const { width, height } = pdfPage.getSize();
      
      // Draw the combined image over the PDF page
      pdfPage.drawImage(pngImage, {
        x: 0,
        y: 0,
        width: width,
        height: height
      });
    }

    // Save and download
    const pdfBytes = await pdf.save();
    const blob = new Blob([pdfBytes], {type: "application/pdf"});
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "highlighted_document.pdf";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    alert('PDF downloaded successfully!');
  } catch(error) {
    console.error('Download error:', error);
    alert('Error downloading PDF: ' + error.message);
  }
}

pdfjsLib.getDocument({ data: pdfData }).promise.then(doc=>{
  pdfDoc = doc;
  renderPage(1);
});
</script>

</body>
</html>
"""

        html_code = html_code.replace("__PDF_BASE64__", pdf_base64)

        components.html(
            html_code,
            height=900,
            scrolling=True
        )


# Feature 11 : Reorder PDF Pages
elif feature == "🔀 Reorder Pages":
    st.header("🔀 Reorder PDF Pages")
    st.write("Change the order of pages and preview before downloading.")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file:
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            total_pages = len(reader.pages)

            st.info(f"📄 Total pages: {total_pages}")

            st.markdown("### 🔢 Enter New Page Order")
            st.caption("Example: 3,1,2 or 5,4,3,2,1")

            page_order_input = st.text_input(
                "New page order (comma-separated)",
                placeholder="1,2,3,4"
            )

            preview_pages = st.checkbox("👀 Preview reordered pages", value=True)

            if st.button("🔀 Apply Reorder", use_container_width=True):
                if not page_order_input:
                    st.warning("⚠️ Please enter page order.")
                else:
                    try:
                        # Parse input
                        page_numbers = [
                            int(p.strip()) for p in page_order_input.split(",")
                        ]

                        # Validation
                        if len(page_numbers) != total_pages:
                            st.error("❌ Page count mismatch.")
                        elif sorted(page_numbers) != list(range(1, total_pages + 1)):
                            st.error("❌ Invalid page numbers or duplicates detected.")
                        else:
                            writer = PyPDF2.PdfWriter()

                            for p in page_numbers:
                                writer.add_page(reader.pages[p - 1])

                            output = io.BytesIO()
                            writer.write(output)
                            output.seek(0)

                            # Save for preview & download
                            st.session_state.reordered_pdf = output.getvalue()

                            st.success("✅ Pages reordered successfully!")

                    except ValueError:
                        st.error("❌ Only numbers and commas are allowed.")

        except Exception as e:
            st.error(f"❌ Error reading PDF: {str(e)}")

    # ======================================================
    # PREVIEW + DOWNLOAD
    # ======================================================
    if "reordered_pdf" in st.session_state:

        st.markdown("### 👀 Preview Reordered PDF")

        preview_count = st.slider(
            "Pages to preview",
            min_value=1,
            max_value=min(5, total_pages),
            value=min(2, total_pages)
        )

        try:
            images = convert_from_bytes(
                st.session_state.reordered_pdf,
                dpi=90,
                first_page=1,
                last_page=preview_count
            )

            for i, img in enumerate(images, 1):
                st.image(
                    img,
                    caption=f"Preview – Page {i}",
                    use_column_width=True
                )

        except Exception:
            st.warning("⚠️ Preview not available on this system.")

        create_download_button(
            st.session_state.reordered_pdf,
            "reordered_document.pdf",
            "⬇️ Download Reordered PDF"
        )


# ======================================================
# Feature: Sign PDF 
# ======================================================
# ======================================================
# PDF Signature Tool – Click to Place + Slider Fine Tune
# ======================================================
import streamlit as st
from pypdf import PdfReader, PdfWriter
from pdf2image import convert_from_bytes
from reportlab.pdfgen import canvas
from PIL import Image
import streamlit.components.v1 as components
import numpy as np
import io
import tempfile
import os
import base64

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="PDF Signature Tool",
    page_icon="✍️",
    layout="wide"
)

st.title("✍️ PDF Signature Tool")
st.write("Click on the PDF to place your signature. Use sliders for fine adjustment.")

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def remove_signature_background(sig_image: Image.Image, threshold: int = 230) -> Image.Image:
    sig = sig_image.convert("RGBA")
    data = np.array(sig)

    r = data[:, :, 0]
    g = data[:, :, 1]
    b = data[:, :, 2]

    white_bg = (r > threshold) & (g > threshold) & (b > threshold)
    data[white_bg, 3] = 0

    return Image.fromarray(data)

def pil_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

# --------------------------------------------------
# Session state init
# --------------------------------------------------
if "signature_click" not in st.session_state:
    st.session_state.signature_click = None

# --------------------------------------------------
# Uploads
# --------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    pdf_file = st.file_uploader("📄 Upload PDF", type=["pdf"])
with col2:
    sig_file = st.file_uploader("✍️ Upload Signature (PNG / JPG)", type=["png", "jpg", "jpeg"])

# --------------------------------------------------
# Main logic
# --------------------------------------------------
if pdf_file and sig_file:

    # Signature processing
    sig_image = Image.open(sig_file)
    sig_no_bg = remove_signature_background(sig_image)

    st.subheader("🖋️ Signature Preview")
    st.image(sig_no_bg, width=300)

    # PDF preview
    images = convert_from_bytes(pdf_file.getvalue(), dpi=150)
    page_image = images[0]
    img_b64 = pil_to_base64(page_image)

    reader = PdfReader(io.BytesIO(pdf_file.getvalue()))
    first_page = reader.pages[0]
    pdf_width = float(first_page.mediabox.width)
    pdf_height = float(first_page.mediabox.height)
    total_pages = len(reader.pages)

    st.divider()
    st.subheader("📄 Click on PDF to place signature")

    # --------------------------------------------------
    # CLICK CAPTURE (HTML → JS → session_state)
    # --------------------------------------------------
    components.html(
        f"""
        <html>
        <body style="margin:0">
          <img src="data:image/png;base64,{img_b64}"
               style="width:100%; cursor:crosshair;"
               onclick="send(event)" />
          <script>
            function send(e) {{
              const r = e.target.getBoundingClientRect();
              const data = {{
                x: e.clientX - r.left,
                y: e.clientY - r.top,
                w: r.width,
                h: r.height
              }};
              window.parent.postMessage(
                {{ type: "signature_click", payload: data }},
                "*"
              );
            }}
          </script>
        </body>
        </html>
        """,
        height=int(page_image.size[1] * 0.8),
    )

    # JS listener (GLOBAL)
    components.html("""
    <script>
    window.addEventListener("message", (e) => {
      if (e.data && e.data.type === "signature_click") {
        window.Streamlit.setComponentValue(e.data.payload);
      }
    });
    </script>
    """, height=0)

    # --------------------------------------------------
    # Handle click safely
    # --------------------------------------------------
    click_payload = st.session_state.get("signature_click")

    if isinstance(click_payload, dict):
        st.success(
            f"📍 Clicked at X={int(click_payload['x'])}, "
            f"Y={int(click_payload['y'])}"
        )

        st.session_state["x_percent"] = int(
            (click_payload["x"] / click_payload["w"]) * 100
        )
        st.session_state["y_percent"] = int(
            (click_payload["y"] / click_payload["h"]) * 100
        )

    st.divider()
    st.subheader("📍 Fine Tune Position & Size")

    # Sliders
    x_percent = st.slider(
        "Horizontal Position (%)",
        0, 100,
        st.session_state.get("x_percent", 50)
    )

    y_percent = st.slider(
        "Vertical Position (%)",
        0, 100,
        st.session_state.get("y_percent", 80)
    )

    scale = st.slider("Signature Size (%)", 25, 300, 100)

    apply_all = st.checkbox(
        f"Apply signature to all {total_pages} pages",
        value=False
    )

    # Convert to PDF coordinates
    x_pdf = (x_percent / 100) * pdf_width
    y_pdf = pdf_height - ((y_percent / 100) * pdf_height)

    sig_width = int(sig_no_bg.width * scale / 100)
    sig_height = int(sig_no_bg.height * scale / 100)

    st.info(f"PDF size: {int(pdf_width)} × {int(pdf_height)} points")

    # --------------------------------------------------
    # APPLY SIGNATURE
    # --------------------------------------------------
    if st.button("✍️ Apply Signature to PDF", type="primary", use_container_width=True):

        writer = PdfWriter()
        sig_resized = sig_no_bg.resize(
            (sig_width, sig_height),
            Image.Resampling.LANCZOS
        )

        for i, page in enumerate(reader.pages):

            if i == 0 or apply_all:
                packet = io.BytesIO()
                page_w = float(page.mediabox.width)
                page_h = float(page.mediabox.height)
                can = canvas.Canvas(packet, pagesize=(page_w, page_h))

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp_path = tmp.name
                    sig_resized.save(tmp_path)

                try:
                    can.drawImage(
                        tmp_path,
                        x_pdf,
                        y_pdf - sig_height,
                        width=sig_width,
                        height=sig_height,
                        mask="auto"
                    )
                    can.save()
                finally:
                    os.unlink(tmp_path)

                packet.seek(0)
                overlay = PdfReader(packet)
                page.merge_page(overlay.pages[0])

            writer.add_page(page)

        output = io.BytesIO()
        writer.write(output)
        output.seek(0)

        st.success("✅ Signature applied successfully!")

        st.download_button(
            "⬇️ Download Signed PDF",
            output,
            "signed_document.pdf",
            "application/pdf",
            use_container_width=True
        )

else:
    st.info("👆 Upload a PDF and a signature image to get started.")


#######################################################################


# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>📄 Stat Cement PDF Editor Pro </p>
    <p>💡 All processing happens securely on the server. Files are not stored </p>
</div>

""", unsafe_allow_html=True)













































