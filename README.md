# TrueFoundry Sales Email Automation

A streamlined email automation service that generates research and personalized emails for B2B prospects using TrueFoundry's LLM gateway.

## 🚀 Quick Deploy to TrueFoundry

### 1. Build Docker Image
```bash
docker build -f Dockerfile.truefoundry -t your-registry/email-automation:latest .
docker push your-registry/email-automation:latest
```

### 2. Deploy on TrueFoundry
- **Name**: `Email Automation Service`
- **Deploy Type**: Docker Image
- **Image URL**: `your-registry/email-automation:latest`
- **Port**: `8080`
- **Protocol**: HTTP
- **Expose**: ✅ Yes

### 3. Environment Variables
```bash
TFY_API_KEY=your_truefoundry_api_key
TFY_REASONING_MODEL=openai-main/gpt-5
TFY_BASE_URL=https://llm-gateway.truefoundry.com
```

## 📁 Project Structure
```
email_v1/
├── email_automation.py      # Core pipeline logic
├── config.py               # Configuration settings  
├── parsing_utils.py        # LLM response parsing
├── unified_app.py          # Combined frontend/backend service
├── streamlit_app.py        # Streamlit UI
├── requirements.txt        # Python dependencies
├── Dockerfile.truefoundry  # Docker image for TrueFoundry
├── karl_martin_prospect.csv # Sample data
├── output/                 # Generated files
└── README.md              # This file
```

## 🔧 How It Works

1. **Upload CSV**: Upload a CSV with columns: `person_name`, `company_name`, `linkedin_url`
2. **Research Generation**: LLM analyzes prospects and generates detailed research
3. **Email Creation**: Personalized emails are created based on research
4. **Download**: Get both research CSV and email TXT files

🌙 **Perfect for overnight batch processing** - Upload large files (50+ prospects) and let the system run overnight with no timeouts!

## 📋 Input Format
CSV file with these columns:
```csv
person_name,company_name,linkedin_url
Karl Martin,integrate.ai,https://www.linkedin.com/in/karlmartin0
```

## 📤 Output Files
- **Research CSV**: Detailed prospect research with 25+ data points
- **Email TXT**: Personalized sales emails for each prospect

## 🌐 Access Your Deployed App
After TrueFoundry deployment:
- **Web Interface**: `https://your-endpoint/`
- **API Docs**: `https://your-endpoint/docs`
- **Health Check**: `https://your-endpoint/health`

## 🛠️ Local Development
```bash
pip install -r requirements.txt
python unified_app.py
```
Open `http://localhost:8080`

## 📝 API Key Configuration
The TrueFoundry API key is currently hardcoded in `config.py`. For production, set the `TFY_API_KEY` environment variable.

## 🔍 Features
- 🚀 **Unlimited batch processing** - No limits on file size
- 🌙 **Overnight processing support** - No timeouts, perfect for large batches  
- 📊 **Chunked processing** for optimal memory usage
- 🛡️ **Robust error handling** and parsing
- 🎯 **Combined frontend/backend** in single service
- 💓 **Health monitoring** endpoint
- 📥 **Downloadable outputs** - research CSV and email TXT files