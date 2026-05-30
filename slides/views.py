from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from groq import Groq
from urllib.parse import quote
import json
import os
import re
import logging
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

modelslab_key = os.getenv('MODLESLAB_API_KEY')
groq_key = os.getenv('GROQ_API_KEY')

groq_client = Groq(api_key=groq_key) if groq_key else None

POLLINATIONS_BASE = 'https://image.pollinations.ai/p'

SYSTEM_PROMPT = """You are a slide deck generator. Given a topic, create 5 presentation slides.
Each slide must have a compelling title and 3-5 bullet points of key content.

Return valid JSON in this exact format (no markdown, no code fences):
{"slides": [{"id": 1, "title": "Slide Title", "content": ["Point 1", "Point 2", "Point 3"]}, ...]}

Make content informative, specific, and well-structured for a presentation."""


def build_prompt(slide):
    parts = [slide.get('title', '')]
    content = slide.get('content', [])
    if content:
        parts.extend(content[:2])
    return ', '.join(parts) or 'presentation slide background'


def build_pollinations_url(slide, index):
    prompt = build_prompt(slide)
    prompt = re.sub(r'[^\w\s,.-]', '', prompt).strip()[:200]
    if not prompt:
        prompt = 'presentation slide background'
    encoded = quote(prompt)
    seed = index + 1
    return f"{POLLINATIONS_BASE}/{encoded}?width=1024&height=768&seed={seed}&nologo=true"


def try_modelslab(prompt, seed):
    if not modelslab_key:
        return None
    try:
        resp = requests.post(
            'https://modelslab.com/api/v7/images/text-to-image',
            json={
                'key': modelslab_key,
                'model_id': 'flux',
                'prompt': prompt,
                'negative_prompt': 'blurry, low quality',
                'width': 1024,
                'height': 768,
                'samples': 1,
                'num_inference_steps': 20,
                'seed': seed,
            },
            timeout=90,
        )
        if resp.status_code not in (200, 201):
            return None
        data = resp.json()
        return data.get('output', [None])[0]
    except Exception:
        logger.exception('ModelsLab failed')
        return None


def generate_slide_image(slide, index):
    prompt = build_prompt(slide)
    seed = index + 1

    result = try_modelslab(prompt, seed)
    if result:
        return result, 'ModelsLab'

    return build_pollinations_url(slide, index), 'Pollinations'


def slide_builder(request):
    return render(request, 'slide_builder.html')


def extract_json(text):
    text = text.strip()
    start = text.find('{"slides"')
    if start < 0:
        start = text.find('"slides"')
        if start < 0:
            raise ValueError('No slides data found')
        start = text.rfind('{', 0, start)
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                text = text[start:i+1]
                break
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    text = re.sub(r'\]\]', r']', text)
    return json.loads(text)


def sse_event(event_type, **data):
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


@csrf_exempt
def generate_slides(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        body = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    topic = (body.get('topic') or '').strip()
    if not topic:
        return JsonResponse({'error': 'Topic is required'}, status=400)

    if not groq_client:
        return JsonResponse({'error': 'GROQ_API_KEY not set. Check your .env file.'}, status=500)

    def stream():
        try:
            yield sse_event('progress', percent=5, message='Generating slide content...')

            completion = groq_client.chat.completions.create(
                model='llama-3.1-8b-instant',
                messages=[
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': f'Generate slides about: {topic}'},
                ],
                temperature=0.7,
                max_tokens=2048,
            )

            text = completion.choices[0].message.content.strip()
            slides_data = extract_json(text)
            slides = slides_data.get('slides', [])

            if not slides:
                yield sse_event('error', message='No slides generated')
                return

            total = len(slides)
            yield sse_event('progress', percent=20, message='Generating cover image...')

            for i, slide in enumerate(slides):
                pct = 20 + int((i + 1) / total * 75)

                if i == 0:
                    yield sse_event('progress', percent=pct, message='Generating cover image...')
                    try:
                        image, provider = generate_slide_image(slide, i)
                        slide['image'] = image
                        yield sse_event('progress', percent=pct, message=f'Cover: {provider}')
                    except Exception:
                        logger.exception('Cover image failed')
                        slide['image'] = build_pollinations_url(slide, i)
                        yield sse_event('progress', percent=pct, message='Cover: Pollinations')
                else:
                    slide['image'] = None
                    yield sse_event('progress', percent=pct, message=f'Slide {i+1} of {total}')

            yield sse_event('progress', percent=98, message='Finalizing...')
            yield sse_event('result', slides=slides)

        except Exception as e:
            yield sse_event('error', message=str(e))

    return StreamingHttpResponse(
        stream(),
        content_type='text/event-stream',
    )
