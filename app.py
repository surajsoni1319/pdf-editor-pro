import streamlit as st
import PyPDF2
from PIL import Image
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import yellow, red, green, blue
import pdf2image
import img2pdf
import os

st.set_page_config(page_title="PDF Editor Pro", page_icon="📄", layout="wide")

# Custom CSS for better UI
st.markdown("""
    <style>
    .main-header {
        font-size: 5rem;
        font-weight: bold;
        text-align: center;
        color: #FF4B4B;
        margin-bottom: 2rem;
    }
    .feature-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
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
        "✨ Highlight Text"
    ]
)

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
    
    uploaded_files = st.file_uploader("Choose PDF files", type=['pdf'], accept_multiple_files=True)
    
    if uploaded_files and len(uploaded_files) > 1:
        st.success(f"✅ {len(uploaded_files)} files uploaded")
        
        # Show file order
        st.write("**Files will be merged in this order:**")
        for i, file in enumerate(uploaded_files, 1):
            st.write(f"{i}. {file.name}")
        
        if st.button("🔗 Merge PDFs", use_container_width=True):
            try:
                merger = PyPDF2.PdfMerger()
                
                for pdf in uploaded_files:
                    merger.append(pdf)
                
                output = io.BytesIO()
                merger.write(output)
                merger.close()
                output.seek(0)
                
                create_download_button(output.getvalue(), "merged_document.pdf", "⬇️ Download Merged PDF")
                st.success("✅ PDFs merged successfully!")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    elif uploaded_files and len(uploaded_files) == 1:
        st.warning("⚠️ Please upload at least 2 PDF files to merge.")

# Feature 2: Split PDF
elif feature == "✂️ Split PDF":
    st.header("✂️ Split PDF into Pages")
    st.write("Split a PDF into individual page files.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file:
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            num_pages = len(reader.pages)
            
            st.info(f"📄 Total pages: {num_pages}")
            
            split_option = st.radio("Split option:", ["Split all pages", "Split specific range"])
            
            if split_option == "Split all pages":
                if st.button("✂️ Split All Pages", use_container_width=True):
                    with st.spinner("Splitting PDF..."):
                        for i in range(num_pages):
                            writer = PyPDF2.PdfWriter()
                            writer.add_page(reader.pages[i])
                            
                            output = io.BytesIO()
                            writer.write(output)
                            output.seek(0)
                            
                            st.download_button(
                                label=f"⬇️ Download Page {i+1}",
                                data=output.getvalue(),
                                file_name=f"page_{i+1}.pdf",
                                mime="application/pdf"
                            )
            
            else:
                col1, col2 = st.columns(2)
                with col1:
                    start_page = st.number_input("Start page", min_value=1, max_value=num_pages, value=1)
                with col2:
                    end_page = st.number_input("End page", min_value=1, max_value=num_pages, value=num_pages)
                
                if st.button("✂️ Split Range", use_container_width=True):
                    writer = PyPDF2.PdfWriter()
                    for i in range(start_page-1, end_page):
                        writer.add_page(reader.pages[i])
                    
                    output = io.BytesIO()
                    writer.write(output)
                    output.seek(0)
                    
                    create_download_button(output.getvalue(), f"pages_{start_page}_to_{end_page}.pdf", "⬇️ Download Split PDF")
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
    st.write("Add text watermark to all pages.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    if uploaded_file:
        watermark_text = st.text_input("Watermark text:", placeholder="CONFIDENTIAL")
        
        col1, col2 = st.columns(2)
        with col1:
            font_size = st.slider("Font size", 10, 100, 40)
        with col2:
            opacity = st.slider("Opacity", 0.1, 1.0, 0.3, 0.1)
        
        if st.button("💧 Add Watermark", use_container_width=True) and watermark_text:
            try:
                # Create watermark
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)
                can.setFillColorRGB(0, 0, 0, opacity)
                can.setFont("Helvetica-Bold", font_size)
                can.saveState()
                can.translate(300, 400)
                can.rotate(45)
                can.drawCentredString(0, 0, watermark_text)
                can.restoreState()
                can.save()
                
                packet.seek(0)
                watermark_pdf = PyPDF2.PdfReader(packet)
                watermark_page = watermark_pdf.pages[0]
                
                # Apply to original PDF
                reader = PyPDF2.PdfReader(uploaded_file)
                writer = PyPDF2.PdfWriter()
                
                for page in reader.pages:
                    page.merge_page(watermark_page)
                    writer.add_page(page)
                
                output = io.BytesIO()
                writer.write(output)
                output.seek(0)
                
                create_download_button(output.getvalue(), "watermarked_document.pdf", "⬇️ Download Watermarked PDF")
                st.success("✅ Watermark added successfully!")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

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


