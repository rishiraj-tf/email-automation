#!/usr/bin/env python3
"""
Unified Application - Single Service Deployment
Combines FastAPI backend with embedded Streamlit frontend
"""

import subprocess
import threading
import time
import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import tempfile
import pandas as pd
from email_automation import EmailAutomationPipeline
from config import PipelineConfig

# Create FastAPI backend inline
backend_app = FastAPI(
    title="Email Automation API",
    description="Backend API for sales email automation",
    version="1.0.0"
)

# Add CORS middleware
backend_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@backend_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "email-automation"}

@backend_app.post("/validate")
async def validate_csv(file: UploadFile = File(...)):
    """Validate uploaded CSV file format"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        content = await file.read()
        await file.seek(0)
        
        # Check if file is empty
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Try to read as CSV
        df = pd.read_csv(file.file)
        
        # Check required columns
        required_columns = ['person_name', 'company_name', 'linkedin_url']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {missing}"
            )
        
        return {
            "valid": True, 
            "rows": len(df),
            "columns": list(df.columns),
            "message": f"Valid CSV with {len(df)} prospects"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@backend_app.post("/process")
async def process_prospects(file: UploadFile = File(...)):
    """Process prospects and generate research and emails"""
    temp_csv_path = None
    try:
        # Validate file first
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            temp_file.write(content)
            temp_csv_path = temp_file.name
        
        # Validate CSV structure
        try:
            df = pd.read_csv(temp_csv_path)
            required_columns = ['person_name', 'company_name', 'linkedin_url']
            if not all(col in df.columns for col in required_columns):
                missing = [col for col in required_columns if col not in df.columns]
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing required columns: {missing}"
                )
        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail="CSV file is empty or invalid")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")
        
        try:
            # Initialize pipeline
            logging.info("Initializing pipeline...")
            config = PipelineConfig.from_env()
            
            # Check API key
            if not config.api_key:
                raise HTTPException(status_code=400, detail="API key not configured")
                
            pipeline = EmailAutomationPipeline(config)
            logging.info(f"Processing {len(df)} prospects...")
            
            # Process the CSV - no timeout limits for overnight batch processing
            result = pipeline.process_csv_file(temp_csv_path)
            logging.info("Pipeline processing completed")
            
            # Read the generated files
            if not os.path.exists(result["research_csv"]):
                raise HTTPException(status_code=500, detail="Research CSV file was not generated")
            
            with open(result["research_csv"], 'r', encoding='utf-8') as f:
                research_csv = f.read()
            
            with open(result["email_txt"], 'r', encoding='utf-8') as f:
                email_txt = f.read()
            
            with open(result["research_md"], 'r', encoding='utf-8') as f:
                research_md = f.read()
            
            return {
                "success": True,
                "research_csv": research_csv,
                "email_txt": email_txt, 
                "research_md": research_md,
                "summary": {
                    "total_prospects": result["total_prospects"],
                    "files_generated": ["research_csv", "research_md", "email_txt"]
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Pipeline processing error: {str(e)}", exc_info=True)
            # Check for common errors
            error_msg = str(e).lower()
            if "api" in error_msg or "openai" in error_msg:
                raise HTTPException(status_code=500, detail=f"LLM API error: {str(e)}")
            elif "timeout" in error_msg:
                raise HTTPException(status_code=408, detail=f"Processing timeout: {str(e)}")
            else:
                raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        # Clean up temp file
        if temp_csv_path and os.path.exists(temp_csv_path):
            try:
                os.unlink(temp_csv_path)
            except:
                pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedApp:
    def __init__(self, port=8080):
        self.port = port
        self.streamlit_process = None
        self.streamlit_port = 8501
        self.backend_port = 8000
        
    def start_streamlit(self):
        """Start Streamlit in a separate process"""
        try:
            logger.info(f"🎨 Starting Streamlit on port {self.streamlit_port}...")
            
            # Start Streamlit with custom config
            env = os.environ.copy()
            env.update({
                'STREAMLIT_SERVER_HEADLESS': 'true',
                'STREAMLIT_SERVER_ENABLE_CORS': 'false',
                'STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION': 'false',
                'STREAMLIT_BROWSER_GATHER_USAGE_STATS': 'false'
            })
            
            self.streamlit_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", 
                "streamlit_app.py",
                "--server.port", str(self.streamlit_port),
                "--server.address", "127.0.0.1",
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false"
            ], env=env)
            
            # Wait for Streamlit to start
            time.sleep(5)
            
            if self.streamlit_process.poll() is None:
                logger.info(f"✅ Streamlit started successfully on port {self.streamlit_port}")
            else:
                logger.error("❌ Streamlit failed to start")
                
        except Exception as e:
            logger.error(f"❌ Failed to start Streamlit: {e}")
    
    def stop_streamlit(self):
        """Stop Streamlit process"""
        if self.streamlit_process:
            try:
                self.streamlit_process.terminate()
                self.streamlit_process.wait(timeout=5)
                logger.info("✅ Streamlit stopped")
            except subprocess.TimeoutExpired:
                self.streamlit_process.kill()
                logger.info("🔧 Streamlit force-killed")
            except Exception as e:
                logger.error(f"❌ Error stopping Streamlit: {e}")

# Create unified FastAPI app
app = FastAPI(
    title="TrueFoundry Email Automation - Unified Service",
    description="Combined frontend and backend service",
    version="1.0.0"
)

# Mount the backend API routes
app.mount("/api", backend_app)

# Initialize unified app manager
unified_manager = UnifiedApp()

@app.on_event("startup")
async def startup_event():
    """Start Streamlit when FastAPI starts"""
    logger.info("🚀 Starting Unified Email Automation Service...")
    
    # Start Streamlit in background thread
    streamlit_thread = threading.Thread(target=unified_manager.start_streamlit)
    streamlit_thread.daemon = True
    streamlit_thread.start()

@app.on_event("shutdown") 
async def shutdown_event():
    """Stop Streamlit when FastAPI shuts down"""
    logger.info("🛑 Shutting down Unified Service...")
    unified_manager.stop_streamlit()

@app.get("/")
async def root():
    """Redirect root to Streamlit frontend"""
    return RedirectResponse(url=f"http://127.0.0.1:{unified_manager.streamlit_port}")

@app.get("/health")
async def health_check():
    """Health check for the unified service"""
    streamlit_healthy = unified_manager.streamlit_process and unified_manager.streamlit_process.poll() is None
    
    return {
        "status": "healthy" if streamlit_healthy else "degraded",
        "services": {
            "backend": "healthy",
            "frontend": "healthy" if streamlit_healthy else "offline"
        },
        "frontend_url": f"http://127.0.0.1:{unified_manager.streamlit_port}",
        "backend_url": f"http://127.0.0.1:{unified_manager.port}/api"
    }

@app.get("/frontend")
async def frontend_proxy():
    """Proxy to Streamlit frontend"""
    return RedirectResponse(url=f"http://127.0.0.1:{unified_manager.streamlit_port}")

def main():
    """Start the unified application"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start Unified Email Automation Service")
    parser.add_argument('--port', type=int, default=8080, help='Port to serve the application')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind to')
    
    args = parser.parse_args()
    
    unified_manager.port = args.port
    
    try:
        logger.info("=" * 60)
        logger.info("🎉 TrueFoundry Email Automation - Unified Service")
        logger.info("=" * 60)
        logger.info(f"🌐 Main Service: http://{args.host}:{args.port}")
        logger.info(f"📖 API Docs: http://{args.host}:{args.port}/docs")
        logger.info(f"📊 Direct Frontend: http://127.0.0.1:{unified_manager.streamlit_port}")
        logger.info(f"📡 Direct Backend API: http://{args.host}:{args.port}/api")
        logger.info("🛑 Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        # Run the unified service
        uvicorn.run(
            "unified_app:app",
            host=args.host,
            port=args.port,
            log_level="info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Service stopped by user")
    except Exception as e:
        logger.error(f"❌ Service failed: {e}")
    finally:
        unified_manager.stop_streamlit()

if __name__ == "__main__":
    main()
