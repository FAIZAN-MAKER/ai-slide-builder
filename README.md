# AI Slide Builder

> Generate professional presentation slides from any topic using AI — powered by Groq, ModelsLab, and Pollinations.

**Live Demo:** [https://ai-slide-builder.onrender.com](https://ai-slide-builder.onrender.com)

---

## Features

- **AI Content Generation** — Enter a topic and Groq (LLaMA 3.1 8B) generates 5 structured slides with titles and bullet points.
- **AI Cover Image** — ModelsLab Stable Diffusion creates a unique cover image for the first slide. Falls back to Pollinations.ai if unavailable.
- **3D Carousel** — Browse slides with a smooth perspective-driven 3D carousel, built with pure CSS transforms.
- **Export** — Download the deck as PDF or individual slides as PNG (ZIP archive) via html2canvas + jsPDF + JSZip.
- **Persist Across Refresh** — Slides are saved to localStorage so your deck survives page reloads. Click "New deck" to reset.
- **Real-time Progress** — Server-Sent Events stream generation progress (content + image) to the UI.
- **Text-only Slides** — Slides 2–5 render as gradient backgrounds to save API credits and avoid rate limits.
- **Responsive** — Tailwind CSS layout adapts from mobile to desktop.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Django 6.0.5 |
| AI Text | Groq (LLaMA 3.1-8B) |
| AI Image | ModelsLab (FLUX) / Pollinations.ai |
| Frontend | Tailwind CSS, Lucide Icons |
| Export | html2canvas, jsPDF, JSZip |
| WSGI | Gunicorn |
| Static Files | Whitenoise |
| Deployment | Render |

---

## Getting Started

### Prerequisites

- Python 3.13+
- API keys for Groq and ModelsLab

### Installation

```bash
git clone https://github.com/your-username/ai-slide-builder.git
cd ai-slide-builder
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=gsk_your_key_here
MODLESLAB_API_KEY=your_key_here
```

Optional variables (set on your hosting platform for production):

```env
SECRET_KEY=your-production-secret-key
DEBUG=False
```

### Run Locally

```bash
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000).

---

## How It Works

1. **User enters a topic** and clicks "Generate slides".
2. **Backend** calls Groq API to produce 5 slides as JSON, streamed via SSE.
3. **Cover image** is generated via ModelsLab (Stable Diffusion). On failure, Pollinations.ai is used.
4. **Frontend** renders slides in a 3D carousel and loads the cover image sequentially.
5. **Slides persist** in localStorage — refresh the page and they're still there.
6. **Export** any time — PDF for the full deck or individual PNGs.

---

## Deployment

This project is deployed on Render. The `Procfile` and Whitenoise config are ready:

```procfile
web: gunicorn aislides.wsgi:application
```

Set environment variables (`SECRET_KEY`, `DEBUG`, `GROQ_API_KEY`, `MODLESLAB_API_KEY`) in your Render dashboard.

---

## Project Structure

```
aislides/              # Django project settings
  settings.py          # Config, env vars, Whitenoise
  urls.py              # Root URL routing
  wsgi.py              # WSGI entrypoint
slides/                # Django app
  views.py             # Groq + ModelsLab + Pollinations logic
templates/
  slide_builder.html   # Single-page frontend
Procfile               # Render process definition
requirements.txt       # Python dependencies
```

---

## License

MIT
