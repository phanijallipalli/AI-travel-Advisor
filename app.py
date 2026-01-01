import streamlit as st
import requests
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

from openai import OpenAI
from io import BytesIO

# --- REPORTLAB IMPORTS (For Professional PDF) ---
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage, PageBreak, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# ---------------- ENV CONFIGURATION ---------------- #
# Load environment variables from a .env file if present
load_dotenv()

def get_env(key):
    """
    Helper to get API keys from either os.getenv (local .env) or st.secrets (Streamlit Cloud)
    """
    val = os.getenv(key)
    if not val:
        if key in st.secrets:
            return st.secrets[key]
        return None
    return val

# --- USER: REPLACE THESE IF NOT USING .ENV ---
OPENAI_KEY = get_env("OPENAI_API_KEY") or "YOUR_OPENAI_KEY_HERE"
UNSPLASH_KEY = get_env("UNSPLASH_ACCESS_KEY") or "YOUR_UNSPLASH_KEY_HERE"
EMAIL_ADDRESS = get_env("EMAIL_ADDRESS") or "YOUR_EMAIL_HERE"
EMAIL_PASSWORD = get_env("EMAIL_PASSWORD") or "YOUR_APP_PASSWORD_HERE"

client = OpenAI(api_key=OPENAI_KEY)

# ---------------- STREAMLIT UI ---------------- #
st.set_page_config(page_title="Luxe AI Travel", page_icon="✈️", layout="centered")

st.markdown("""
<style>
    .main {background-color: #f5f7f9;}
    h1 {color: #1A237E;}
    .stButton>button {width: 100%; background-color: #1A237E; color: white; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

st.title("✈️ Luxe AI Travel Agent")
st.markdown("### The Complete Planner: Timeline, Logistics, Food & Maps")

with st.form("travel_form"):
    col1, col2 = st.columns(2)
    with col1:
        source = st.text_input("Source City", "New York")
        destination = st.text_input("Destination", "Paris")
        days = st.number_input("Duration (Days)", 3, 14, 5)
    with col2:
        budget = st.selectbox("Budget", ["Standard", "High-End", "Luxury"])
        travelers = st.number_input("Travelers", 1, 10, 2)
        trip_type = st.selectbox("Vibe", ["Relaxing", "Adventure", "Cultural", "Foodie", "Family"])
    
    email = st.text_input("Email Address for Delivery")
    submit_btn = st.form_submit_button("✨ Generate Full Itinerary")

# ---------------- HELPER FUNCTIONS ---------------- #

def fetch_image(query):
    """Downloads a high-quality image from Unsplash based on the specific location."""
    try:
        url = "https://api.unsplash.com/search/photos"
        headers = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}
        # Landscape orientation fits our table layout best
        params = {"query": query, "per_page": 1, "orientation": "landscape"}
        
        res = requests.get(url, headers=headers, params=params)
        data = res.json()
        
        if data.get("results"):
            img_url = data["results"][0]["urls"]["small"]
            img_response = requests.get(img_url)
            return BytesIO(img_response.content)
    except Exception as e:
        print(f"Image Error for {query}: {e}")
    return None

# ---------------- OPENAI LOGIC ---------------- #

def generate_itinerary_text():
    prompt = f"""
    Act as an elite travel planner. Create a highly detailed {days}-day itinerary for {destination} departing from {source}.
    
    Vibe: {trip_type} | Budget: {budget} | Travelers: {travelers}

    **CRITICAL STRUCTURE INSTRUCTIONS:**
    
    1. **GENERAL INFO:**
    TITLE: Journey to {destination}
    OVERVIEW: (Brief summary of the experience)
    GETTING_THERE: (Best Flights/Trains/Road route from {source})

    2. **TIMELINE (Summary Table):**
    TIMELINE_START
    Day 1: [Brief Summary]
    Day 2: [Brief Summary]
    (etc...)
    TIMELINE_END

    3. **DETAILED STOPS (Visual Guide):**
    ITINERARY_START
    
    Day 1: [Day Title]
    
    STOP: [Exact Name of Place/Activity - Morning]
    BEST TIME: [e.g. 09:00 AM]
    LOGISTICS: [How to get here from city center/last spot]
    DETAILS: [Description with Google Maps Link like <link href="http://maps.google.com/?q={destination}+PLACE_NAME" color="blue">Open Map</link>]
    FOOD: 
    - 🥗 Veg: [Name] (Cuisine)
    - 🍗 Non-Veg: [Name] (Cuisine)
    
    STOP: [Exact Name of Place/Activity - Afternoon]
    BEST TIME: [e.g. 2:00 PM]
    LOGISTICS: [How to get here]
    DETAILS: [Description with Map Link]
    FOOD: 
    - 🥗 Veg: [Name] (Cuisine)
    - 🍗 Non-Veg: [Name] (Cuisine)
    
    (Repeat STOP structure for all days)
    ITINERARY_END
    
    TRAVEL_TIPS:
    (Bullet points on safety, weather, packing)
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Use gpt-3.5-turbo if on a budget
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI Error: {e}")
        return None

# ---------------- ARTISTIC PDF GENERATION ---------------- #

def add_page_design(canvas, doc):
    """Adds the border and footer to every PDF page."""
    canvas.saveState()
    navy = colors.HexColor("#1A237E")
    w, h = A4
    
    # Border
    canvas.setStrokeColor(navy)
    canvas.setLineWidth(2)
    canvas.rect(20, 20, w-40, h-40) 
    
    # Footer
    canvas.setFont('Times-Italic', 9)
    canvas.setFillColor(colors.darkgrey)
    canvas.drawString(40, 30, f"Prepared for {email}")
    canvas.drawRightString(w-40, 30, "Luxe AI Travel Agent")
    canvas.restoreState()

def create_stop_table(story, lines, style_body, style_bold):
    """Creates the Side-by-Side [Text | Image] layout for a specific stop."""
    place_name = ""
    details_text = []
    
    # Parse the buffer lines to format text nicely
    for line in lines:
        if line.startswith("STOP:"):
            place_name = line.replace("STOP:", "").strip()
            details_text.append(Paragraph(f"<b>📍 {place_name}</b>", style_bold))
        elif line.startswith("BEST TIME:"):
            details_text.append(Paragraph(f"<b>🕒 Best Time:</b> {line.replace('BEST TIME:', '')}", style_body))
        elif line.startswith("LOGISTICS:"):
             details_text.append(Paragraph(f"<b>🚕 Logistics:</b> {line.replace('LOGISTICS:', '')}", style_body))
        elif line.startswith("FOOD:"):
            details_text.append(Spacer(1, 5))
            details_text.append(Paragraph("<b>🍽️ Nearby Eats:</b>", style_bold))
        else:
            # Contains description or food items
            details_text.append(Paragraph(line, style_body))
            
    # Fetch Image specific to THIS place
    st.write(f"📸 Finding photo for: {place_name}...") # UI Feedback
    search_query = f"{destination} {place_name}"
    img_bytes = fetch_image(search_query)
    
    img_col = []
    if img_bytes:
        img = ReportLabImage(img_bytes)
        # Resize image to fit the column width (2.8 inches)
        aspect = img.imageHeight / img.imageWidth
        target_w = 2.8 * inch
        img.drawWidth = target_w
        img.drawHeight = target_w * aspect
        img_col = [img]
    
    # Table: Text Left (4 inch) | Image Right (2.8 inch)
    data = [[details_text, img_col]]
    t = Table(data, colWidths=[4*inch, 2.8*inch])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    story.append(KeepTogether(t)) # Keep text/image together on one page
    story.append(Spacer(1, 15))

def generate_pdf(text_content):
    pdf_filename = f"Itinerary_{destination.replace(' ', '_')}.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    # Define Styles
    style_title = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=26, textColor=colors.HexColor("#1A237E"), spaceAfter=20, alignment=1)
    style_header = ParagraphStyle('Header', parent=styles['Heading2'], fontSize=16, textColor=colors.HexColor("#D4AF37"), spaceBefore=15)
    style_day = ParagraphStyle('Day', parent=styles['Heading3'], fontSize=14, textColor=colors.HexColor("#1A237E"), spaceBefore=15, spaceAfter=5)
    style_body = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14)
    style_bold = ParagraphStyle('Bold', parent=styles['Normal'], fontSize=10, leading=14, fontName='Helvetica-Bold')

    story = []
    lines = text_content.split('\n')
    
    current_day = ""
    stop_buffer = []
    timeline_data = [["Day", "Summary"]] # Header for Timeline Table
    
    section_state = "NORMAL" # State Machine: NORMAL, TIMELINE, ITINERARY
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # --- SECTION DETECTION ---
        if "TIMELINE_START" in line:
            section_state = "TIMELINE"
            story.append(Paragraph("Trip at a Glance", style_header))
            story.append(Spacer(1, 10))
            continue
        elif "TIMELINE_END" in line:
            section_state = "NORMAL"
            # Render Timeline Table
            t = Table(timeline_data, colWidths=[1*inch, 5.5*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A237E")), # Blue Header
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ]))
            story.append(t)
            story.append(PageBreak()) # Start details on new page
            continue

        elif "ITINERARY_START" in line:
            section_state = "ITINERARY"
            story.append(Paragraph("Detailed Visual Guide", style_header))
            continue
        elif "ITINERARY_END" in line:
            section_state = "NORMAL"
            # Flush any remaining buffer
            if stop_buffer:
                create_stop_table(story, stop_buffer, style_body, style_bold)
            continue
            
        # --- CONTENT PARSING BASED ON STATE ---
        
        if section_state == "TIMELINE":
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    timeline_data.append([parts[0].strip(), parts[1].strip()])

        elif section_state == "ITINERARY":
            if line.startswith("Day"):
                current_day = line
                story.append(Paragraph(current_day, style_day))
                story.append(Paragraph("<hr width='100%' color='#D4AF37'/>", style_body))
            
            elif line.startswith("STOP:"):
                # If we have a previous stop buffered, print it first
                if stop_buffer:
                    create_stop_table(story, stop_buffer, style_body, style_bold)
                    stop_buffer = [] 
                stop_buffer.append(line) 
            else:
                if stop_buffer:
                    stop_buffer.append(line)

        else: # NORMAL STATE (Overview, Logistics, Tips)
            if "TITLE:" in line:
                story.append(Paragraph(line.replace("TITLE:", "").strip(), style_title))
            elif "OVERVIEW:" in line:
                story.append(Paragraph("Trip Overview", style_header))
            elif "GETTING_THERE:" in line:
                story.append(Spacer(1, 10))
                story.append(Paragraph(f"How to Reach {destination}", style_header))
            elif "TRAVEL_TIPS:" in line:
                story.append(PageBreak())
                story.append(Paragraph("Travel Tips", style_header))
            else:
                story.append(Paragraph(line, style_body))

    doc.build(story, onFirstPage=add_page_design, onLaterPages=add_page_design)
    return pdf_filename

# ---------------- EMAIL LOGIC ---------------- #

def send_email_with_pdf(pdf_path, target_email):
    msg = EmailMessage()
    msg["Subject"] = f"Your Detailed Itinerary: {destination} ✈️"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = target_email
    msg.set_content(f"Hi there,\n\nPlease find attached your custom AI-generated travel plan for {destination}.\n\nEnjoy your trip!\n\nBest,\nLuxe AI Travel Agent")
    
    with open(pdf_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(pdf_path)
        msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=file_name)
    
    try:
        # Connect to Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email Error: {e}")
        return False

# ---------------- MAIN APP EXECUTION ---------------- #

if submit_btn:
    if not all([source, destination, email]):
        st.error("⚠️ Please fill in Source, Destination, and Email.")
    elif not all([OPENAI_KEY, UNSPLASH_KEY, EMAIL_PASSWORD]):
        st.error("⚠️ API Keys missing. Please check your .env file or script configuration.")
    else:
        with st.spinner(f"🧠 Designing the perfect {days}-day trip to {destination}..."):
            
            # 1. Generate Text (The Brain)
            raw_text = generate_itinerary_text()
            
            if raw_text:
                # 2. Create PDF (The Artist)
                pdf_file = generate_pdf(raw_text)
                
                # 3. Send Email (The Courier)
                if send_email_with_pdf(pdf_file, email):
                    st.success(f"✅ Itinerary successfully sent to {email}!")
                    
                    # 4. Allow Download
                    with open(pdf_file, "rb") as f:
                        st.download_button("⬇️ Download PDF Now", f, file_name=pdf_file)