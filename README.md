<img width="1440" height="1102" alt="image" src="https://github.com/user-attachments/assets/5da9005a-ff8e-4849-bc6a-a541da8b09b5" />

<img width="1440" height="1356" alt="image" src="https://github.com/user-attachments/assets/28218824-84b8-4251-ae3d-71dce8c01dd3" />

quickapply/
├── backend/                  ← Start here. This is your strength.
│   ├── main.py               ← FastAPI entry point
│   ├── .env                  ← API keys, DB URL (never commit this)
│   ├── requirements.txt
│   ├── models/
│   │   ├── user.py
│   │   ├── profile.py
│   │   └── application.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── profile.py
│   │   └── documents.py
│   ├── services/
│   │   ├── pdf_parser.py     ← PyMuPDF + pdfplumber
│   │   ├── profile_agent.py  ← Calls Claude to structure parsed text
│   │   └── writing_agent.py  ← Calls Claude to generate documents
│   └── storage/
│       └── file_handler.py   ← Saves uploaded files to disk/S3
│
├── frontend/                 ← Touch this in Week 8
│   ├── app/
│   └── components/
│
└── README.md


