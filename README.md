# TrafficSense: AI-Powered Multi-Camera Traffic Violation Detection System

TrafficSense is an automated traffic monitoring and violation detection platform. It processes feeds from multiple cameras simultaneously to track vehicles, detect infractions, and generate structured evidence for law enforcement and urban management.

## Technical Specifications

* **Detection Core**: Ultralytics YOLOv8s (Small)
* **Deep Learning Runtime**: PyTorch Nightly (CUDA accelerated)
* **Hardware Environment**: NVIDIA GeForce RTX 5050 Laptop GPU

## Key Features

* **Multi-Camera Processing**: Coordinated handling of multiple simultaneous video feeds.
* **Real-Time Tracking**: Continuous vehicle tracking across frames.
* **Configurable Rule Engine**: Customizable parameters for red-light running, wrong-way driving, and illegal lane changes.
* **Automated Evidence Collection**: Automatic snapshots and tracking histories.
* **Full-Stack Architecture**: Includes a FastAPI backend for RESTful API management and an interactive HTML/JS frontend dashboard.

## Quick Start Guide

### 1. Environment Configuration
Clone the repository and navigate to the project root directory:
```bash
git clone [https://github.com/your-repo/TrafficSense.git](https://github.com/your-repo/TrafficSense.git)
cd TrafficSense

### 2. Backend Setup
The backend serves as the centralized server for receiving violation events.

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r Requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

### 3. AI Engine Setup
Ensure you install PyTorch Nightly with CUDA support matching your RTX 5050 setup.

```bash
# Return to the root directory
cd ..
pip install -r requirements.txt
python ai_engine/main_engine.py

