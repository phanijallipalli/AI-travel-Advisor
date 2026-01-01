import streamlit as st
import openai
import requests
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Luxe AI Travel Agent",
    page_icon="✈️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1A237E 0%, #D4AF37 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background: linear-gradient(135deg, #1A237E 0%, #D4AF37 100%);
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        border: none;
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        background: #e8f5e9;
        border-left: 4px solid #4caf50;
        border-radius: 4px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def fetch_unsplash_image(query, width=800, height=600):
    """Fetch a specific image from Unsplash based on query"""
    try:
        access_key = os.getenv('UNSPLASH_ACCESS_KEY')
        if not access_key:
            # Fallback to source URL if no API key
            return f"https://source.unsplash.com/{width}x{height}/?{query}"
        
        url = f"https://api.unsplash.com/search/photos"
        params = {
            'query': query,
            'per_page': 1,
            'orientation': 'landscape'
        }
        headers = {'Authorization': f'Client-ID {access_key}'}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                return data['results'][0]['urls']['regular']
        
        # Fallback
        return f"https://source.unsplash.com/{width}x{height}/?{query}"
    except Exception as e:
        st.warning(f"Image fetch warning: {str(e)}")
        return f"https://source.unsplash.com/{width}x{height}/?{query}"

def download_image(url):
    """Download image and return as PIL Image"""
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            return img
        return None
    except Exception as e:
        st.warning(f"Image download error: {str(e)}")
        return None

def generate_itinerary(source, destination, days, budget, travelers, vibe):
    """Generate structured itinerary using OpenAI"""
    
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    if not openai.api_key:
        raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file")
    
    prompt = f"""You are a luxury travel agent. Create a detailed {days}-day itinerary for a trip from {source} to {destination}.

Budget: ${budget}
Travelers: {travelers}
Vibe: {vibe}

STRICT FORMAT - Return ONLY valid JSON with this exact structure:

{{
  "trip_summary": {{
    "title": "Trip title",
    "overview": "Brief overview paragraph"
  }},
  "daily_overview": [
    {{"day": 1, "theme": "Day theme title"}},
    {{"day": 2, "theme": "Day theme title"}}
  ],
  "detailed_itinerary": [
    {{
      "day": 1,
      "stops": [
        {{
          "time_of_day": "Morning",
          "title": "Activity/Place Name",
          "description": "Detailed description",
          "best_time": "09:00 AM",
          "logistics": "Transportation details",
          "food_options": {{
            "veg": {{"name": "Restaurant Name", "dish": "Dish name"}},
            "non_veg": {{"name": "Restaurant Name", "dish": "Dish name"}}
          }},
          "search_query": "Specific location name for image search"
        }}
      ]
    }}
  ]
}}

Requirements:
- Create {days} days with 2-3 stops per day (Morning/Afternoon/Evening)
- Each stop must have ALL fields filled
- Food options must be REAL restaurant names in {destination}
- search_query should be specific (e.g., "Eiffel Tower Paris" not just "Paris")
- Logistics should include actual transport options
- Best times should be realistic

Return ONLY the JSON, no other text."""

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a luxury travel planning assistant. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up potential markdown formatting
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        itinerary = json.loads(content.strip())
        return itinerary
    
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse AI response. Error: {str(e)}")
        raise
    except Exception as e:
        st.error(f"OpenAI API Error: {str(e)}")
        raise

def create_pdf(itinerary, destination, days, budget):
    """Generate professional PDF with images"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1A237E'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#D4AF37'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leading=14
    )
    
    # Title page
    story.append(Paragraph(f"✈️ {itinerary['trip_summary']['title']}", title_style))
    story.append(Paragraph(itinerary['trip_summary']['overview'], body_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Trip overview table
    overview_data = [
        ['Destination', destination],
        ['Duration', f'{days} Days'],
        ['Budget', f'${budget:,}'],
    ]
    
    overview_table = Table(overview_data, colWidths=[2*inch, 4*inch])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1A237E')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    
    story.append(overview_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Daily overview
    story.append(Paragraph("📅 Trip at a Glance", heading_style))
    
    daily_data = [['Day', 'Theme']]
    for day_overview in itinerary['daily_overview']:
        daily_data.append([f"Day {day_overview['day']}", day_overview['theme']])
    
    daily_table = Table(daily_data, colWidths=[1*inch, 5*inch])
    daily_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D4AF37')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    
    story.append(daily_table)
    story.append(PageBreak())
    
    # Detailed itinerary with images
    for day_data in itinerary['detailed_itinerary']:
        story.append(Paragraph(f"Day {day_data['day']}", title_style))
        
        for stop in day_data['stops']:
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph(f"⏰ {stop['time_of_day']}: {stop['title']}", heading_style))
            
            # Try to fetch and add image
            try:
                img_url = fetch_unsplash_image(stop['search_query'])
                img = download_image(img_url)
                
                if img:
                    # Save to temp buffer
                    img_buffer = BytesIO()
                    img = img.convert('RGB')
                    img.thumbnail((400, 300))
                    img.save(img_buffer, format='JPEG')
                    img_buffer.seek(0)
                    
                    rl_img = RLImage(img_buffer, width=4*inch, height=3*inch)
                    story.append(rl_img)
                    story.append(Spacer(1, 0.1*inch))
            except Exception as e:
                st.warning(f"Could not add image for {stop['title']}: {str(e)}")
            
            # Details
            story.append(Paragraph(f"<b>Description:</b> {stop['description']}", body_style))
            story.append(Paragraph(f"<b>Best Time:</b> {stop['best_time']}", body_style))
            story.append(Paragraph(f"<b>Getting There:</b> {stop['logistics']}", body_style))
            
            # Food options
            veg = stop['food_options']['veg']
            non_veg = stop['food_options']['non_veg']
            story.append(Paragraph(f"<b>🥗 Veg Option:</b> {veg['dish']} at {veg['name']}", body_style))
            story.append(Paragraph(f"<b>🍗 Non-Veg Option:</b> {non_veg['dish']} at {non_veg['name']}", body_style))
            
            story.append(Paragraph(f"<b>📍 Google Maps:</b> <link href='[https://www.google.com/maps/search/?api=1&query=](https://www.google.com/maps/search/?api=1&query=){stop['search_query'].replace(' ', '+')}'>Search Location</link>", body_style))
            
            story.append(Spacer(1, 0.2*inch))
        
        story.append(PageBreak())
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def send_email(recipient_email, pdf_buffer, destination):
    """Send email with PDF attachment"""
    
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    
    if not sender_email or not sender_password:
        raise ValueError("Email credentials not found. Set SENDER_EMAIL and SENDER_PASSWORD in .env")
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = f'Your Luxury {destination} Itinerary ✈️'
    
    body = f"""
    Dear Traveler,
    
    Your personalized luxury itinerary for {destination} is ready!
    
    Please find your complete travel guide attached as a PDF.
    
    Bon Voyage!
    
    - The Luxe AI Travel Team
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach PDF
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(pdf_buffer.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{destination}_Itinerary.pdf"')
    msg.attach(part)
    
    # Send email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email sending failed: {str(e)}")
        return False

# Main App
def main():
    st.markdown('<h1 class="main-header">✈️ Luxe AI Travel Agent</h1>', unsafe_allow_html=True)
    st.markdown("### Curated Luxury Experiences, Powered by AI")
    
    # Check for API keys
    if not os.getenv('OPENAI_API_KEY'):
        st.error("⚠️ OpenAI API key not configured. Please add OPENAI_API_KEY to your .env file")
        st.info("Create a .env file with: OPENAI_API_KEY=your_key_here")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        source = st.text_input("🏠 From City", placeholder="New York")
        destination = st.text_input("🌍 Destination", placeholder="Paris")
        days = st.slider("📅 Duration (Days)", 1, 14, 5)
        budget = st.number_input("💰 Budget (USD)", min_value=500, max_value=100000, value=5000, step=500)
    
    with col2:
        travelers = st.number_input("👥 Number of Travelers", min_value=1, max_value=20, value=2)
        vibe = st.selectbox("✨ Travel Vibe", [
            "Luxury & Relaxation",
            "Adventure & Exploration",
            "Cultural Immersion",
            "Romantic Getaway",
            "Family Fun",
            "Foodie Paradise"
        ])
        email = st.text_input("📧 Email Address", placeholder="your@email.com")
    
    st.markdown("---")
    
    if st.button("🚀 Generate My Dream Itinerary"):
        if not all([source, destination, email]):
            st.error("Please fill in all required fields!")
            return
        
        try:
            with st.spinner("✨ AI is crafting your perfect journey..."):
                # Generate itinerary
                itinerary = generate_itinerary(source, destination, days, budget, travelers, vibe)
                st.success("✅ Itinerary generated!")
            
            with st.spinner("📸 Fetching stunning visuals..."):
                # Create PDF
                pdf_buffer = create_pdf(itinerary, destination, days, budget)
                st.success("✅ PDF created!")

                # --- NEW CODE START: Save PDF locally ---
                local_filename = f"{destination}_Luxury_Itinerary.pdf"
                with open(local_filename, "wb") as f:
                    f.write(pdf_buffer.getvalue())
                st.info(f"💾 PDF saved locally as: {local_filename}")
                # --- NEW CODE END ---
            
            with st.spinner("📧 Sending to your inbox..."):
                # Send email
                if send_email(email, pdf_buffer, destination):
                    st.markdown(f"""
                    <div class="success-box">
                        <h3>🎉 Success!</h3>
                        <p>Your luxury itinerary has been sent to <b>{email}</b></p>
                        <p>Check your inbox for your personalized travel guide!</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Offer download
                    pdf_buffer.seek(0)
                    st.download_button(
                        label="📥 Download PDF Now",
                        data=pdf_buffer,
                        file_name=f"{destination}_Luxury_Itinerary.pdf",
                        mime="application/pdf"
                    )
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Tip: Make sure your .env file contains valid API keys")

if __name__ == "__main__":
    main()