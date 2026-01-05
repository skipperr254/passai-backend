# PassAI Backend - Material Processing Service

FastAPI service for extracting text from study materials (PDF, DOCX, PPTX, Images, Text).

---

## 📋 Overview

This backend handles text extraction from documents uploaded to Supabase Storage. After the frontend uploads files, it calls this API to process them and extract text content.

## 🚀 Features

- **Multi-Format Text Extraction**:
  - PDF documents (PyPDF2)
  - Word documents (.docx)
  - PowerPoint presentations (.pptx)
  - Images with OCR (Tesseract)
  - Plain text files

- **Supabase Integration**:
  - Downloads from Supabase Storage
  - Updates database status
  - Real-time processing notifications

- **Authentication**: JWT-based auth via Supabase
- **Error Handling**: Comprehensive error logging
- **Status Tracking**: PROCESSING → READY/ERROR

---

## 📁 Project Structure

```
passai-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── health.py              # Health check endpoint
│   │       └── process_material.py    # Main processing endpoint
│   ├── core/
│   │   ├── config.py                  # Configuration settings
│   │   ├── constants.py               # App constants
│   │   └── security.py                # JWT authentication
│   ├── models/
│   │   └── material.py                # Pydantic models
│   ├── repositories/
│   │   └── material_repository.py     # Database operations
│   ├── services/
│   │   ├── pdf.py                     # PDF text extraction
│   │   ├── docx.py                    # DOCX text extraction
│   │   ├── pptx.py                    # PPTX text extraction
│   │   ├── image.py                   # Image OCR
│   │   └── text.py                    # Text file handling
│   └── utils/
│       └── supabase.py                # Supabase client
├── requirements.txt
└── README.md
```

---

## 🛠️ Setup

### Prerequisites
- **Python** 3.9+
- **Tesseract OCR** (for image processing)
  - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
  - macOS: `brew install tesseract`
  - Linux: `apt-get install tesseract-ocr`

### Installation

1. **Navigate to backend**
```bash
cd passai-backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**

Create `.env` file:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_JWT_SECRET=your_jwt_secret
CORS_ORIGINS=http://localhost:5173
ENVIRONMENT=development
TESSERACT_CMD=  # Optional: custom tesseract path
```

5. **Start development server**
```bash
uvicorn app.main:app --reload --port 8000
```

Server runs at: `http://localhost:8000`

---

## 📡 API Reference

### POST `/api/v1/process-material`
Extract text from uploaded material.

**Authentication**: Bearer token (JWT from Supabase)

**Request Body**:
```json
{
  "material_id": "uuid-of-material",
  "storage_path": "user-id/subject-id/filename.pdf"
}
```

**Response**:
```json
{
  "success": true,
  "material_id": "uuid",
  "text_length": 5432,
  "file_type": "pdf",
  "processing_time": 1250,
  "message": "Material processed successfully"
}
```

**Status Updates**:
- Initial: `PROCESSING`
- Success: `READY` (text saved to database)
- Failure: `ERROR` (error message saved)

### GET `/api/v1/health`
Health check endpoint.
{
  "status": "healthy",
  "timestamp": "2025-01-02T10:30:00Z"
}
```

## 🔄 Processing Flow

1. **Frontend uploads file** directly to Supabase Storage
2. **Frontend creates record** in `study_materials` table with `processing_status='pending'`
3. **Frontend calls** `/process-material` endpoint
4. **Backend processes**:
   - Verifies user owns the material
   - Downloads file from Supabase Storage
   - Extracts text based on file type
   - Saves extracted text to database
   - Updates status to `ready`
5. **Frontend receives update** via Supabase Realtime subscription

## 🧪 Testing

Test the API using curl:

```bash
curl -X POST http://localhost:8000/api/v1/process-material \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "material_id": "your-material-id",
    "storage_path": "path/to/file.pdf"
  }'
```

## 📝 Database Schema

The backend expects this table structure:

```sql
CREATE TABLE study_materials (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  subject_id UUID NOT NULL,
  file_name TEXT NOT NULL,
  file_type TEXT NOT NULL,
  file_size INTEGER NOT NULL,
  storage_path TEXT NOT NULL,
  text_content TEXT,
  processing_status TEXT DEFAULT 'pending',
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 🚨 Error Handling

---

## 🚨 Error Handling

**HTTP Status Codes**:
- `200` - Success
- `400` - Invalid request
- `401` - Unauthorized  
- `404` - Material not found
- `500` - Processing error

Errors are logged and saved to `study_materials.error_message`.

---

## 🚢 Deployment (Render)

See [render.yaml](./render.yaml) for configuration.

1. Create Web Service on Render
2. Connect GitHub repository
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables
5. Deploy!

---

## 📦 Dependencies

Core packages:
- **FastAPI** - Web framework
- **Supabase** - Database & storage
- **PyPDF2** - PDF processing
- **python-docx** - Word documents
- **python-pptx** - PowerPoint
- **Pillow** + **pytesseract** - OCR
- **python-jose** - JWT auth
- **uvicorn** - ASGI server

---

## 🔒 Security

- **JWT Authentication**: Supabase token validation
- **User Verification**: Users can only process their materials
- **Environment Variables**: Secure credential storage
- **CORS**: Restricted origins

---

## 📚 Related

- [Main Project README](../README.md)
- [Frontend README](../passai-study/README.md)
- [Database Migrations](../passai-study/supabase/migrations/)

---

**Built with ❤️ using FastAPI**