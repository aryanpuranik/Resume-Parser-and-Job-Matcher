import streamlit as st
import os
import re
import spacy
from pdfminer.high_level import extract_text
import requests
import time
from bs4 import BeautifulSoup
from anthropic import Anthropic

# Page configuration
st.set_page_config(page_title="📄 AI-Powered Job Finder", layout="wide")
st.title("📄 AI-Powered Job Finder")
st.write("Upload your resume and get matched with job opportunities!")

# Initialize Anthropic Client (Claude API)
anthropic_api_key = "API Key"
client = Anthropic(api_key=anthropic_api_key)

# Load NLP model - make this optional to prevent immediate loading errors
@st.cache_resource
def load_nlp_model():
    try:
        return spacy.load("en_core_web_lg")
    except:
        st.warning("SpaCy model not found. Some features may be limited.")
        return None

nlp = load_nlp_model()

# Function to extract text from a PDF
def extract_resume_text(pdf_bytes):
    try:
        with open("temp_resume.pdf", "wb") as f:
            f.write(pdf_bytes)
        return extract_text("temp_resume.pdf")
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return ""

# Identify resume domain (tech vs non-tech) using Claude AI with expanded industry recognition
def identify_resume_domain(resume_text):
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": f"""Analyze this resume and determine if it's for a technical or non-technical role.
                    Return just "technical" or "non-technical", and the primary industry domain.
                    
                    For industry, be specific and choose from categories including but not limited to:
                    - software development
                    - data science
                    - artificial intelligence
                    - cybersecurity
                    - healthcare
                    - pharmaceuticals
                    - biotech
                    - finance
                    - banking
                    - insurance
                    - real estate
                    - education
                    - marketing
                    - advertising
                    - media
                    - entertainment
                    - hospitality
                    - retail
                    - e-commerce
                    - manufacturing
                    - construction
                    - logistics
                    - transportation
                    - telecommunications
                    - energy
                    - environmental
                    - legal
                    - consulting
                    - human resources
                    - government
                    - nonprofit
                    - consumer goods
                    - agriculture
                    - automotive
                    
                    Format: domain_type|industry
                    Example: technical|software development or non-technical|healthcare
                    
                    Resume:
                    {resume_text}"""
                }
            ]
        )
        domain_info = response.content[0].text.strip()
        # Extract domain parts
        parts = domain_info.split('|')
        if len(parts) >= 2:
            return {
                "type": parts[0].strip().lower(),
                "industry": parts[1].strip().lower()
            }
        return {
            "type": "technical" if "technical" in domain_info.lower() else "non-technical", 
            "industry": "general"
        }
    except Exception as e:
        st.error(f"Error identifying resume domain: {e}")
        return {"type": "unknown", "industry": "general"}

# Extract past job titles with emphasis on timeline and role specificity
def extract_job_titles_detailed(resume_text):
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"""Extract ALL job titles from this resume with the following details:
                    1. Include the exact job title as written
                    2. For each job title, note if it's current or past
                    3. Include the industry/domain for each role
                    4. Add any level indicator (junior, senior, etc.)
                    
                    Format your response as a JSON array of objects with these fields:
                    - title: The exact job title
                    - current: true/false
                    - industry: The industry/domain
                    - level: Junior/Mid/Senior/Executive (if determinable)
                    
                    DO NOT include any explanatory text. ONLY return the JSON array.
                    
                    Resume:
                    {resume_text}"""
                }
            ]
        )
        
        response_text = response.content[0].text.strip()
        
        # Find JSON content between triple backticks if present
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            import json
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Try to parse as JSON directly if not in backticks
        try:
            import json
            return json.loads(response_text)
        except:
            # If JSON parsing fails, return a structured placeholder
            return [{"title": "Could not parse job titles", "current": False, "industry": "unknown", "level": "unknown"}]
            
    except Exception as e:
        st.error(f"Error extracting job titles: {e}")
        return [{"title": "Error extracting job titles", "current": False, "industry": "unknown", "level": "unknown"}]

# Extract key resume attributes using Claude AI
def extract_key_resume_attributes(resume_text, domain_info, job_titles):
    try:
        # Prepare job titles information for Claude
        job_titles_text = "\n".join([
            f"- {job['title']} " + 
            f"({'Current' if job['current'] else 'Past'}, {job['industry']}, {job['level']})"
            for job in job_titles
        ])
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": f"""Analyze this resume for a {domain_info['type']} role in the {domain_info['industry']} industry.
                    
                    The identified job titles are:
                    {job_titles_text}
                    
                    Extract the following key attributes in a structured format:
                    
                    1. Professional Skills (technical and soft skills)
                    2. Experience Level (entry, mid, senior)
                    3. Core Expertise Areas (main domains of expertise)
                    4. Industries (sectors the person has worked in)
                    5. Education Background
                    6. Key Achievements
                    7. Years of Experience
                    8. Related Job Titles (other roles this person would be qualified for)
                    
                    Format your response as JSON with these category keys. For each category, provide an array of values.
                    
                    Resume:
                    {resume_text}"""
                }
            ]
        )
        
        # Extract the JSON part from Claude's response
        response_text = response.content[0].text
        
        # Find JSON content between triple backticks if present
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            import json
            try:
                return json.loads(json_match.group(1))
            except:
                pass
                
        # If no JSON found or parsing failed, try to extract structured data using regex
        attributes = {}
        categories = [
            "Professional Skills", "Experience Level", "Core Expertise Areas", 
            "Industries", "Education Background", "Key Achievements",
            "Years of Experience", "Related Job Titles"
        ]
        
        for category in categories:
            pattern = rf'{category}[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)'
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                # Convert to list by splitting on commas, semicolons, or newlines
                items = re.split(r'[,;\n]+', match.group(1).strip())
                attributes[category] = [item.strip() for item in items if item.strip()]
            else:
                attributes[category] = []
                
        return attributes
        
    except Exception as e:
        st.error(f"Error calling Claude API for resume attributes: {e}")
        return {
            "Professional Skills": [],
            "Experience Level": [],
            "Core Expertise Areas": [],
            "Industries": [],
            "Education Background": [],
            "Key Achievements": [],
            "Years of Experience": [],
            "Related Job Titles": []
        }

# Get resume summary
def summarize_resume(resume_text, domain_info):
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=800,
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize the following resume for a {domain_info['type']} role in the {domain_info['industry']} industry. Focus on career trajectory, key skills, and qualifications. Be concise and highlight the most impressive aspects:\n\n{resume_text}"
                }
            ]
        )
        return response.content[0].text
    except Exception as e:
        st.error(f"Error calling Claude API for summarization: {e}")
        return "Could not generate resume summary. Please check your API key."

# Get resume improvements
def get_resume_improvements(resume_text, domain_info):
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"You are a professional resume reviewer for {domain_info['type']} roles in the {domain_info['industry']} industry. Based on the following resume, suggest 3-5 specific areas of improvement. Focus on content, structure, and presentation. Be constructive and specific. Here's the resume text:\n\n{resume_text}"
                }
            ]
        )
        return response.content[0].text
    except Exception as e:
        st.error(f"Error calling Claude API for improvements: {e}")
        return "Could not generate improvement suggestions. Please check your API key."

# Extract Contact Info
def extract_contact_info(text):
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    phone_pattern = r'\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{4}'
    linkedin_pattern = r'linkedin\.com/in/[a-zA-Z0-9_-]+'
    
    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)
    linkedin = re.findall(linkedin_pattern, text)
    
    return {
        "Email": emails[0] if emails else "Not Found",
        "Phone": phones[0] if phones else "Not Found",
        "LinkedIn": linkedin[0] if linkedin else "Not Found"
    }

# Generate search terms based on job titles and domain
def generate_search_terms(job_titles, resume_attributes, domain_info):
    search_terms = []
    
    # Always prioritize the most recent job titles
    current_jobs = [job["title"] for job in job_titles if job.get("current", False)]
    if current_jobs:
        search_terms.extend(current_jobs[:2])
    
    # Add past job titles if we need more terms
    past_jobs = [job["title"] for job in job_titles if not job.get("current", False)]
    if past_jobs and len(search_terms) < 2:
        search_terms.extend(past_jobs[:2 - len(search_terms)])
    
    # Add related job titles from attributes
    if "Related Job Titles" in resume_attributes and resume_attributes["Related Job Titles"] and len(search_terms) < 3:
        search_terms.extend(resume_attributes["Related Job Titles"][:3 - len(search_terms)])
    
    # Add industry-specific terms for non-tech roles
    if domain_info["type"] == "non-technical" and domain_info["industry"] != "general":
        industry_term = f"{domain_info['industry']} {job_titles[0]['title'] if job_titles else ''}"
        search_terms.append(industry_term.strip())
    
    # Ensure we have at least one search term
    if not search_terms:
        search_terms = ["entry level"] if "entry" in str(resume_attributes.get("Experience Level", [])).lower() else ["experienced"]
    
    # Remove duplicates and limit
    return list(set(search_terms))[:4]


def find_job_details(job_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }
    
    try:
        response = requests.get(job_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return "Description not available"
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Try to extract job description
        description_element = soup.find("div", class_="description__text")
        if description_element:
            description = description_element.get_text(strip=True)
        else:
            # If not found, try alternative selectors
            description_element = soup.find("section", class_="show-more-less-html")
            description = description_element.get_text(strip=True) if description_element else "Description not available"
            
        return description
    except Exception as e:
        return "Description not available"

def find_linkedin_jobs(search_terms, location, domain_info, num_jobs=6):
    job_results = []
    
    # Safety check
    if not search_terms:
        return job_results
    
    st.write(f"Searching for jobs using terms: {', '.join(search_terms)}")
    
    for search_term in search_terms:
        search_query = search_term.replace(" ", "%20")
        location_query = location.replace(" ", "%20")
        
        # Add domain/industry context for non-tech roles
        if domain_info["type"] == "non-technical" and domain_info["industry"] != "general":
            if domain_info["industry"] not in search_term.lower():
                search_query = f"{domain_info['industry']}%20{search_query}"
        
        url = f"https://www.linkedin.com/jobs/search?keywords={search_query}&location={location_query}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.find_all("div", class_="base-card")[:num_jobs]

            for job in job_cards:
                try:
                    title_tag = job.find("h3", class_="base-search-card__title")
                    company_tag = job.find("h4", class_="base-search-card__subtitle")
                    location_tag = job.find("span", class_="job-search-card__location")
                    link_tag = job.find("a", class_="base-card__full-link")
                    
                    # Check if we already have this job to avoid duplicates
                    job_title_text = title_tag.text.strip() if title_tag else "Not Found"
                    company_text = company_tag.text.strip() if company_tag else "Not Found"
                    job_link = link_tag["href"] if link_tag else "#"
                    
                    # Simple duplicate check
                    duplicate = False
                    for existing_job in job_results:
                        if (existing_job["Job Title"] == job_title_text and 
                            existing_job["Company"] == company_text):
                            duplicate = True
                            break
                    
                    if not duplicate:
                        description = find_job_details(job_link)
                        
                        job_results.append({
                            "Job Title": job_title_text,
                            "Company": company_text,
                            "Location": location_tag.text.strip() if location_tag else location,
                            "Description": description,
                            "Job Link": job_link,
                            "Search Term": search_term
                        })
                except:
                    # Skip this job card if there's an error parsing it
                    continue

            # Add a small delay between requests
            time.sleep(1)
        
        except Exception as e:
            st.warning(f"Error scraping jobs for {search_term}")
            continue
    
    return job_results

# Use Claude to analyze job matches with domain awareness
def analyze_job_match(resume_attributes, job_info, domain_info, job_titles):
    try:
        # Format resume attributes for Claude
        attributes_text = "\n".join([
            f"{key}:\n- " + "\n- ".join(values) 
            for key, values in resume_attributes.items() if values
        ])
        
        # Format job titles specifically
        job_titles_text = "\n".join([
            f"- {job['title']} ({'Current' if job['current'] else 'Past'}, {job['industry']}, {job['level']})"
            for job in job_titles
        ])
        
        job_text = f"""
        Job Title: {job_info['Job Title']}
        Company: {job_info['Company']}
        Location: {job_info['Location']}
        Description: {job_info['Description']}
        """
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=800,
            messages=[
                {
                    "role": "user",
                    "content": f"""Analyze how well the following job matches with the candidate's profile. This candidate has a {domain_info['type']} background in the {domain_info['industry']} industry.
                    
                    Candidate's Job History:
                    {job_titles_text}
                    
                    Resume Attributes:
                    {attributes_text}
                    
                    Job Information:
                    {job_text}
                    
                    Score the match from 0-100 with 100 being a perfect match. Put extra emphasis on past job titles and industry alignment.
                    
                    Then provide exactly three bullet points explaining why this job is or isn't a good match.
                    
                    Format your response as follows:
                    Match Score: [number]
                    
                    Key Match Factors:
                    • [first point]
                    • [second point]
                    • [third point]
                    """
                }
            ]
        )
        
        # Parse the response to extract score and match factors
        response_text = response.content[0].text
        
        # Extract score
        score_match = re.search(r'Match Score:\s*(\d+)', response_text)
        score = int(score_match.group(1)) if score_match else 50
        
        # Extract key factors
        factors_section = re.search(r'Key Match Factors:(.*?)($|(?=\n\n))', response_text, re.DOTALL)
        factors = []
        if factors_section:
            # Extract bullet points
            bullet_points = re.findall(r'•\s*(.*?)(?=\n•|\n\n|$)', factors_section.group(1), re.DOTALL)
            factors = [point.strip() for point in bullet_points if point.strip()]
        
        return {
            "score": score,
            "factors": factors if factors else ["No specific factors identified"]
        }
    except Exception as e:
        st.error(f"Error analyzing job match: {str(e)}")
        return {
            "score": 50,  # Default middle score
            "factors": ["Could not analyze match details"]
        }

# Rank jobs using Claude's analysis with domain awareness
def rank_jobs(job_listings, resume_attributes, domain_info, job_titles):
    if not job_listings:
        return []
    
    ranked_jobs = []
    
    # Create a progress bar
    job_analysis_progress = st.progress(0)
    total_jobs = len(job_listings)
    
    # Analyze each job
    for i, job in enumerate(job_listings):
        job_analysis_progress.progress((i) / total_jobs)
        match_result = analyze_job_match(resume_attributes, job, domain_info, job_titles)
        ranked_jobs.append({
            "job": job,
            "score": match_result["score"],
            "factors": match_result["factors"]
        })
        # Update progress
        job_analysis_progress.progress((i + 1) / total_jobs)
    
    # Sort by score descending
    ranked_jobs.sort(key=lambda x: x["score"], reverse=True)
    
    # Complete the progress
    job_analysis_progress.progress(1.0)
    
    return ranked_jobs

# Streamlit UI
st.sidebar.title("Resume Analyzer")
st.sidebar.write("Upload your resume to find matching jobs")

uploaded_file = st.sidebar.file_uploader("Upload Resume (PDF)", type=["pdf"])

# Improved location selection UI
st.sidebar.write("📍 Job Location")

# Popular locations with better UI
popular_locations = [
    "Remote", "New York", "San Francisco", "Chicago", 
    "Seattle", "Boston", "Austin", "London", "Toronto"
]

# Create a container for the location buttons with better styling
st.sidebar.write("Popular locations:")

# Create a 3-column layout for location buttons
col1, col2, col3 = st.sidebar.columns(3)
columns = [col1, col2, col3]

# Session state to track selected location
if 'selected_location' not in st.session_state:
    st.session_state.selected_location = "Remote"

# Generate location buttons with improved UI
for i, loc in enumerate(popular_locations):
    col_idx = i % 3
    is_selected = st.session_state.selected_location == loc
    
    # Determine button style based on selection state
    button_label = loc
    
    # Create the button with conditional styling
    if columns[col_idx].button(
        button_label, 
        key=f"loc_{i}",
        use_container_width=True,
        type="primary" if is_selected else "secondary"
    ):
        st.session_state.selected_location = loc
        st.rerun()

# Allow custom location input
st.sidebar.write("Or enter custom location:")
custom_location = st.sidebar.text_input(
    "City, State, Country",
    value=st.session_state.selected_location,
    key="custom_location"
)

# Update selected location if custom input changes
if custom_location != st.session_state.selected_location:
    st.session_state.selected_location = custom_location

# Get final location value
location = st.session_state.selected_location

if uploaded_file and st.sidebar.button("🔍 Analyze Resume"):
    try:
        with st.spinner("Processing your resume..."):
            # Extract text
            resume_text = extract_resume_text(uploaded_file.getvalue())
            
            if not resume_text:
                st.error("Could not extract text from the uploaded PDF. Please try another file.")
            else:
                # Step 1: Identify resume domain (tech vs non-tech)
                with st.spinner("Identifying resume domain..."):
                    domain_info = identify_resume_domain(resume_text)
                    st.write(f"📊 Resume Domain: **{domain_info['type'].title()}** in **{domain_info['industry'].title()}** industry")
                
                # Step 2: Extract job titles with detailed information
                with st.spinner("Extracting job history..."):
                    job_titles = extract_job_titles_detailed(resume_text)
                
                # Step 3: Extract all other resume attributes
                with st.spinner("Extracting key resume attributes..."):
                    resume_attributes = extract_key_resume_attributes(resume_text, domain_info, job_titles)
                    
                # Step 4: Generate insights
                with st.spinner("Generating insights..."):
                    resume_summary = summarize_resume(resume_text, domain_info)
                    improvement_suggestions = get_resume_improvements(resume_text, domain_info)
                
                # Step 5: Extract contact info
                contact_info = extract_contact_info(resume_text)
                
                # Step 6: Generate search terms based on job titles and domain
                search_terms = generate_search_terms(job_titles, resume_attributes, domain_info)
                
                # Step 7: Fetch job listings based on search terms and domain
                with st.spinner(f"Finding matching jobs in {location}..."):
                    job_listings = find_linkedin_jobs(search_terms, location, domain_info)
                    
                    if job_listings:
                        with st.spinner("Analyzing job matches... This may take a moment"):
                            ranked_jobs = rank_jobs(job_listings, resume_attributes, domain_info, job_titles)
                    else:
                        ranked_jobs = []
                
                # Display results in two columns
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # Resume Domain
                    st.subheader("🌐 Resume Profile")
                    st.write(f"**Domain:** {domain_info['type'].title()}")
                    st.write(f"**Industry:** {domain_info['industry'].title()}")
                    
                    # Job History
                    st.subheader("💼 Job History")
                    
                    for job in job_titles:
                        status = "🟢 Current" if job.get("current", False) else "🔵 Past"
                        st.write(f"{status}: **{job['title']}** ({job['industry']}, {job['level']})")
                    
                    # Resume Summary
                    st.subheader("🌟 Resume Summary")
                    st.info(resume_summary)
                    
                    # Improvement Suggestions
                    st.subheader("✨ Areas for Improvement")
                    st.info(improvement_suggestions)
                    
                    # Key Resume Attributes (in expanders to save space)
                    st.subheader("📊 Key Resume Attributes")
                    
                    for category, items in resume_attributes.items():
                        if items and category not in ["Years of Experience", "Experience Level"]:
                            with st.expander(f"{category}"):
                                st.write(", ".join(items))
                    
                    # Contact Info
                    if contact_info:
                        with st.expander("📝 Contact Information"):
                            for key, value in contact_info.items():
                                if value != "Not Found":
                                    st.write(f"{key}: {value}")
                
                with col2:
                    st.subheader("🎯 Job Matches")
                    
                    # Show search location and terms used
                    st.caption(f"Location: **{location}**")
                    st.caption(f"Search terms: {', '.join(search_terms)}")
                    
                    if ranked_jobs:
                        for job_match in ranked_jobs:
                            job = job_match["job"]
                            score = job_match["score"]
                            factors = job_match["factors"]
                            
                            # Create a color based on the score (from red to green)
                            color = f"hsl({min(score * 1.2, 120)}, 70%, 50%)"
                            
                            with st.expander(f"🚀 {job['Job Title']} at {job['Company']} - Match: {score}%"):
                                st.markdown(f"""
                                **Company:** {job['Company']}  
                                **Location:** {job['Location']}  
                                **Found via search term:** {job['Search Term']}
                                
                                **Match Analysis:**
                                """)
                                
                                # Display match factors
                                for factor in factors:
                                    st.markdown(f"- {factor}")
                                
                                # Display job description preview (truncated)
                                if job['Description'] and job['Description'] != "Description not available":
                                    preview = job['Description'][:300] + "..." if len(job['Description']) > 300 else job['Description']
                                    st.markdown("**Description Preview:**")
                                    st.markdown(f"{preview}")
                                
                                # Apply button
                                st.markdown(f"[Apply for this Job]({job['Job Link']})")
                    else:
                        st.error(f"No job matches found in {location}. Try a different location or update your resume with more relevant keywords.")
                
                st.success("🎉 Analysis Complete! Your resume has been analyzed and job matches have been found.")
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Please try again with a different resume file or contact support.")
