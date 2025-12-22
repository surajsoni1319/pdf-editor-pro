import streamlit as st
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
        "🔀 Reorder Pages"

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

# Feature 6: Extract Text
elif feature == "📝 Extract Text":
    st.header("📝 Extract Text from PDF")
    st.write("Extract all text content from your PDF.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file:
        if st.button("📝 Extract Text", use_container_width=True):
            try:
                reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                
                with st.spinner("Extracting text..."):
                    for i, page in enumerate(reader.pages, 1):
                        page_text = page.extract_text()
                        text += f"\n\n--- Page {i} ---\n\n{page_text}"
                
                st.text_area("Extracted Text:", text, height=400)
                
                # Download as text file
                st.download_button(
                    label="⬇️ Download as TXT",
                    data=text,
                    file_name="extracted_text.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
                st.success(f"✅ Text extracted from {len(reader.pages)} pages!")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Feature: Reorder PDF Pages
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

# Feature 7: Extract Images
elif feature == "🖼️ Extract Images":
    st.header("🖼️ Extract Images from PDF")
    st.write("Extract all images from your PDF.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file:
        if st.button("🖼️ Extract Images", use_container_width=True):
            try:
                reader = PyPDF2.PdfReader(uploaded_file)
                image_count = 0
                
                with st.spinner("Extracting images..."):
                    for page_num, page in enumerate(reader.pages, 1):
                        if '/XObject' in page['/Resources']:
                            xObject = page['/Resources']['/XObject'].get_object()
                            
                            for obj in xObject:
                                if xObject[obj]['/Subtype'] == '/Image':
                                    image_count += 1
                                    st.write(f"Found image on page {page_num}")
                
                if image_count > 0:
                    st.success(f"✅ Found {image_count} images!")
                    st.info("💡 For full image extraction, consider using specialized tools like 'pdfplumber' or 'pdf2image'")
                else:
                    st.warning("⚠️ No images found in this PDF.")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Feature 8: Compress PDF
elif feature == "🗜️ Compress PDF":
    st.header("🗜️ Compress PDF Size")
    st.write("Reduce PDF file size by removing unnecessary data.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file:
        original_size = len(uploaded_file.getvalue()) / 1024  # KB
        st.info(f"📊 Original size: {original_size:.2f} KB")
        
        if st.button("🗜️ Compress PDF", use_container_width=True):
            try:
                reader = PyPDF2.PdfReader(uploaded_file)
                writer = PyPDF2.PdfWriter()
                
                for page in reader.pages:
                    page.compress_content_streams()
                    writer.add_page(page)
                
                output = io.BytesIO()
                writer.write(output)
                output.seek(0)
                
                compressed_size = len(output.getvalue()) / 1024  # KB
                reduction = ((original_size - compressed_size) / original_size) * 100
                
                st.success(f"✅ Compressed size: {compressed_size:.2f} KB")
                st.success(f"📉 Reduced by: {reduction:.1f}%")
                
                create_download_button(output.getvalue(), "compressed_document.pdf", "⬇️ Download Compressed PDF")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Feature 9: PDF to Images
elif feature == "📸 PDF to Images":
    st.header("📸 Convert PDF to Images")
    st.write("Convert each page to an image file.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file:
        col1, col2 = st.columns(2)
        with col1:
            image_format = st.selectbox("Image format", ["PNG", "JPEG"])
        with col2:
            dpi = st.slider("Quality (DPI)", 72, 300, 150)
        
        if st.button("📸 Convert to Images", use_container_width=True):
            try:
                st.info("⚠️ Note: This feature requires 'poppler' to be installed on the server. For local use, install: `pip install pdf2image` and poppler-utils")
                st.warning("This feature may not work on Streamlit Cloud without additional configuration.")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Feature 10: Highlight Text
elif feature == "✨ Highlight Text":
    st.header("✨ Highlight Areas in PDF")
    st.write("Add colored highlights to specific areas.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file:
        st.info("📄 Upload your PDF first")
        
        col1, col2 = st.columns(2)
        with col1:
            page_to_highlight = st.number_input("Page number", min_value=1, value=1)
            highlight_color = st.selectbox("Highlight color", ["Yellow", "Green", "Red", "Blue"])
        
        with col2:
            x_pos = st.slider("X position", 0, 600, 100)
            y_pos = st.slider("Y position", 0, 800, 600)
        
        width = st.slider("Width", 50, 500, 200)
        height = st.slider("Height", 10, 200, 50)
        
        if st.button("✨ Add Highlight", use_container_width=True):
            try:
                # Color mapping
                color_map = {
                    "Yellow": yellow,
                    "Green": green,
                    "Red": red,
                    "Blue": blue
                }
                
                # Create highlight overlay
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)
                can.setFillColor(color_map[highlight_color], alpha=0.3)
                can.rect(x_pos, y_pos, width, height, fill=1, stroke=0)
                can.save()
                
                packet.seek(0)
                overlay_pdf = PyPDF2.PdfReader(packet)
                overlay_page = overlay_pdf.pages[0]
                
                # Apply to original PDF
                reader = PyPDF2.PdfReader(uploaded_file)
                writer = PyPDF2.PdfWriter()
                
                for i, page in enumerate(reader.pages, 1):
                    if i == page_to_highlight:
                        page.merge_page(overlay_page)
                    writer.add_page(page)
                
                output = io.BytesIO()
                writer.write(output)
                output.seek(0)
                
                create_download_button(output.getvalue(), "highlighted_document.pdf", "⬇️ Download Highlighted PDF")
                st.success("✅ Highlight added successfully!")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>📄 Stat Cement PDF Editor Pro </p>
    <p>💡 All processing happens in your browser. Files are not stored.</p>
</div>

""", unsafe_allow_html=True)























