#!/usr/bin/env python3
"""
FastAPI server for Sports Card Grader
Provides REST API endpoints for the React frontend
"""

import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add current directory to path to import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import grading system with fallback handling
try:
    from sports_card_grader import CardAnalyzer, GradingSystem
except ImportError as e:
    print(f"Warning: Could not import full analyzer: {e}")
    print("Using fallback implementation")
    from sports_card_grader import CardAnalyzer, GradingSystem

app = FastAPI(
    title="Sports Card Grader API",
    description="API for analyzing sports card quality and predicting grades",
    version="1.0.0"
)

# Enable CORS for React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (React build will go here later)
if os.path.exists("frontend/build"):
    app.mount("/static", StaticFiles(directory="frontend/build"), name="static")

# Store for ongoing analysis requests (in production, use Redis or database)
analysis_store: Dict[str, Dict[str, Any]] = {}

class AnalysisStatus(BaseModel):
    """Model for analysis status response"""
    analysis_id: str
    status: str  # "pending", "processing", "completed", "error"
    progress: Optional[int] = None
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    debug_info: Optional[Dict[str, Any]] = None

class AnalysisResult(BaseModel):
    """Model for analysis result"""
    analysis_id: str
    predicted_grade: int
    grade_description: str
    overall_score: float
    confidence_level: str
    component_breakdown: Dict[str, Any]
    psa_compliance: Dict[str, Any]
    strengths: list
    weaknesses: list
    improvement_suggestions: list
    centering_evaluation: Optional[Dict[str, Any]] = None
    debug_info: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Sports Card Grader API is running", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    """Detailed health check with system status"""
    try:
        # Test if we can import and create analyzer
        analyzer = CardAnalyzer()
        grader = GradingSystem()
        
        return {
            "status": "healthy",
            "message": "All systems operational",
            "backend_available": True,
            "opencv_available": hasattr(analyzer, 'analyze_edges'),
            "grading_system_available": hasattr(grader, 'generate_detailed_report')
        }
    except Exception as e:
        # Log the full error internally but don't expose stack trace to users
        print(f"Health check error: {e}")
        return {
            "status": "degraded", 
            "message": "System check failed - backend components unavailable",
            "backend_available": False
        }

@app.post("/api/analyze", response_model=Dict[str, str])
async def upload_and_analyze(file: UploadFile = File(...)):
    """
    Upload a card image and start analysis
    Returns analysis_id for tracking progress
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Generate unique analysis ID
    analysis_id = str(uuid.uuid4())
    
    # Initialize analysis status
    analysis_store[analysis_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Analysis queued",
        "filename": file.filename,
        "debug_info": {
            "file_size": 0,
            "file_type": file.content_type,
            "analysis_steps": []
        }
    }
    
    try:
        # Read and save uploaded file
        content = await file.read()
        analysis_store[analysis_id]["debug_info"]["file_size"] = len(content)
        
        # Create temporary file for analysis
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Update status to processing
        analysis_store[analysis_id].update({
            "status": "processing",
            "progress": 10,
            "message": "Initializing analysis...",
        })
        analysis_store[analysis_id]["debug_info"]["analysis_steps"].append("File uploaded and saved")
        
        # Initialize analyzer and grading system
        analyzer = CardAnalyzer()
        grader = GradingSystem()
        
        analysis_store[analysis_id].update({
            "progress": 20,
            "message": "Loading image..."
        })
        analysis_store[analysis_id]["debug_info"]["analysis_steps"].append("Analyzer initialized")
        
        # Load image
        if not analyzer.load_image(temp_file_path):
            analysis_store[analysis_id].update({
                "status": "error",
                "message": "Failed to load image for analysis"
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not process image file"
            )
        
        analysis_store[analysis_id].update({
            "progress": 40,
            "message": "Analyzing card components..."
        })
        analysis_store[analysis_id]["debug_info"]["analysis_steps"].append("Image loaded successfully")
        
        # Perform analysis
        analysis_results = analyzer.analyze_all()
        
        analysis_store[analysis_id].update({
            "progress": 70,
            "message": "Generating grading report..."
        })
        analysis_store[analysis_id]["debug_info"]["analysis_steps"].append("Analysis completed")
        analysis_store[analysis_id]["debug_info"]["raw_analysis"] = analysis_results
        
        # Generate grading report
        report = grader.generate_detailed_report(analysis_results)
        
        analysis_store[analysis_id].update({
            "progress": 90,
            "message": "Finalizing results..."
        })
        analysis_store[analysis_id]["debug_info"]["analysis_steps"].append("Report generated")
        
        # Add company comparison
        company_comparison = grader.compare_to_standards(analysis_results, "PSA")
        report['company_comparison'] = company_comparison
        
        # Convert numpy types to Python native types for JSON serialization
        def convert_numpy_types(obj):
            if hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(v) for v in obj]
            else:
                return obj
        
        report = convert_numpy_types(report)
        
        # Complete analysis
        analysis_store[analysis_id].update({
            "status": "completed",
            "progress": 100,
            "message": "Analysis complete",
            "result": report
        })
        analysis_store[analysis_id]["debug_info"]["analysis_steps"].append("Analysis completed successfully")
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        return {"analysis_id": analysis_id, "status": "processing"}
        
    except Exception as e:
        # Handle analysis errors
        # Log the full error internally but don't expose details to users
        print(f"Analysis error: {e}")
        
        analysis_store[analysis_id].update({
            "status": "error",
            "message": "Analysis failed - please try again with a different image"
        })
        analysis_store[analysis_id]["debug_info"]["error"] = "Internal processing error"
        
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed - please try again with a different image"
        )

@app.get("/api/analysis/{analysis_id}", response_model=AnalysisStatus)
async def get_analysis_status(analysis_id: str):
    """
    Get the status of an analysis request
    """
    if analysis_id not in analysis_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    analysis_data = analysis_store[analysis_id]
    
    return AnalysisStatus(
        analysis_id=analysis_id,
        status=analysis_data["status"],
        progress=analysis_data.get("progress"),
        message=analysis_data.get("message"),
        result=analysis_data.get("result"),
        debug_info=analysis_data.get("debug_info")
    )

@app.get("/api/analysis/{analysis_id}/debug")
async def get_analysis_debug_info(analysis_id: str):
    """
    Get detailed debug information for an analysis
    """
    if analysis_id not in analysis_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    analysis_data = analysis_store[analysis_id]
    
    return {
        "analysis_id": analysis_id,
        "debug_info": analysis_data.get("debug_info", {}),
        "full_status": analysis_data
    }

@app.delete("/api/analysis/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """
    Delete analysis data (cleanup)
    """
    if analysis_id not in analysis_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    del analysis_store[analysis_id]
    return {"message": "Analysis data deleted"}

@app.get("/api/analyses")
async def list_analyses():
    """
    List all analyses (for debugging)
    """
    return {
        "total": len(analysis_store),
        "analyses": [
            {
                "analysis_id": aid,
                "status": data["status"],
                "filename": data.get("filename"),
                "progress": data.get("progress")
            }
            for aid, data in analysis_store.items()
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🏆 Starting Sports Card Grader API Server...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/api/health")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )