"""Hybrid chatbot response generation for the Gram Panchayat portal."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Iterable, List, Optional, Tuple

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .models import Application, Complaint, ElectricityBill, PropertyTaxRecord, WaterBill


DEVA_RE = re.compile(r'[\u0900-\u097F]')
APPLICATION_RE = re.compile(r'\bGP[A-Z]{4}\d{8,}\b', re.IGNORECASE)
COMPLAINT_RE = re.compile(r'\bCMP\d{8,}\b', re.IGNORECASE)

MAX_REPLY_LENGTH = 1200
HISTORY_WINDOW = max(2, int(getattr(settings, 'CHATBOT_HISTORY_LIMIT', 8) or 8))


SERVICE_ACTIONS = {
    'income_certificate': {
        'service': 'income_certificate',
        'title': 'Income Certificate Application',
        'url_name': 'apply_income_certificate',
        'steps': [
            'Confirm applicant details',
            'Fill income details',
            'Upload required documents',
            'Submit application',
        ],
        'prefill': ['name', 'email', 'phone'],
    },
    'birth_certificate': {
        'service': 'birth_certificate',
        'title': 'Birth Certificate Application',
        'url_name': 'apply_birth_certificate',
        'steps': [
            'Enter child details',
            'Enter parent details',
            'Upload supporting documents',
            'Submit application',
        ],
        'prefill': ['name', 'email', 'phone'],
    },
    'death_certificate': {
        'service': 'death_certificate',
        'title': 'Death Certificate Application',
        'url_name': 'apply_death_certificate',
        'steps': [
            'Enter deceased details',
            'Add informant details',
            'Upload supporting documents',
            'Submit application',
        ],
        'prefill': ['name', 'email', 'phone'],
    },
    'complaint': {
        'service': 'complaint',
        'title': 'File Complaint',
        'url_name': 'file_complaint',
        'steps': [
            'Choose category',
            'Describe issue',
            'Upload evidence (optional)',
            'Submit complaint',
        ],
        'prefill': ['name', 'email', 'phone'],
    },
    'electricity_bill': {
        'service': 'electricity_bill',
        'title': 'Electricity Bill Service',
        'url_name': 'electricity_bill_service',
        'steps': [
            'Enter consumer number',
            'Verify bill details',
            'Proceed with payment',
        ],
        'prefill': ['name', 'email', 'phone'],
    },
    'water_bill': {
        'service': 'water_bill',
        'title': 'Water Bill Service',
        'url_name': 'water_bill_service',
        'steps': [
            'Enter connection number',
            'Verify bill details',
            'Proceed with payment',
        ],
        'prefill': ['name', 'email', 'phone'],
    },
    'property_tax': {
        'service': 'property_tax',
        'title': 'Property Tax Service',
        'url_name': 'property_tax_service',
        'steps': [
            'Search property',
            'Verify dues',
            'Proceed with payment',
        ],
        'prefill': ['name', 'email', 'phone'],
    },
}

SUGGESTIONS = {
    'en': {
        'welcome': ['Apply Certificate', 'Check Status', 'Pay Bill', 'Required Documents'],
        'certificate': ['Apply Income Certificate', 'Apply Birth Certificate', 'Apply Death Certificate'],
        'status': ['Track Application', 'Track Complaint', 'Check Bill Status'],
        'bill': ['Pay Electricity Bill', 'Pay Water Bill', 'Pay Property Tax'],
        'complaint': ['File Complaint', 'Track Complaint', 'Complaint Status'],
        'documents': ['Required Documents', 'Apply Certificate', 'Track Application'],
    },
    'hi': {
        'welcome': ['प्रमाणपत्र आवेदन', 'स्थिति देखें', 'बिल भुगतान', 'दस्तावेज़'],
        'certificate': ['आय प्रमाणपत्र', 'जन्म प्रमाणपत्र', 'मृत्यु प्रमाणपत्र'],
        'status': ['आवेदन स्थिति', 'शिकायत स्थिति', 'बिल स्थिति'],
        'bill': ['बिजली बिल', 'पानी बिल', 'प्रॉपर्टी टैक्स'],
        'complaint': ['शिकायत दर्ज करें', 'शिकायत ट्रैक करें', 'शिकायत स्थिति'],
        'documents': ['आवश्यक दस्तावेज़', 'प्रमाणपत्र आवेदन', 'आवेदन स्थिति'],
    },
    'mr': {
        'welcome': ['प्रमाणपत्र अर्ज', 'स्थिती तपासा', 'बिल भरणा', 'कागदपत्रे'],
        'certificate': ['उत्पन्न प्रमाणपत्र', 'जन्म प्रमाणपत्र', 'मृत्यू प्रमाणपत्र'],
        'status': ['अर्ज स्थिती', 'तक्रार स्थिती', 'बिल स्थिती'],
        'bill': ['वीज बिल', 'पाणी बिल', 'मालमत्ता कर'],
        'complaint': ['तक्रार नोंदवा', 'तक्रार ट्रॅक करा', 'तक्रार स्थिती'],
        'documents': ['आवश्यक कागदपत्रे', 'प्रमाणपत्र अर्ज', 'अर्ज स्थिती'],
    },
}

HELP_COPY = {
    'en': {
        'fallback': 'I can help with certificates, complaints, bills, application status, and OTP/login help. Please try asking in a different way.',
        'docs': 'For applying certificates, required documents are:\n- Aadhaar Card\n- Address Proof\n- Passport-size Photo\n- Supporting documents',
        'apply': 'You can apply for certificates from the Services section. Choose the exact certificate type and submit the form.',
        'status': 'I can help you check application, complaint, and bill status. If you have a GP or CMP number, share it for exact tracking.',
        'bill': 'You can pay electricity, water, and property tax bills from the Services section.',
        'complaint': 'You can file a complaint from the Services section and then track it from My Complaints.',
        'login': 'For OTP or login issues, use the login page and click Resend OTP if needed.',
    },
    'hi': {
        'fallback': 'मैं प्रमाणपत्र, शिकायत, बिल, आवेदन स्थिति और OTP/लॉगिन में मदद कर सकता हूँ। कृपया थोड़ा अलग तरीके से पूछें।',
        'docs': 'प्रमाणपत्र आवेदन के लिए आवश्यक दस्तावेज़:\n- आधार कार्ड\n- पता प्रमाण\n- पासपोर्ट साइज फोटो\n- सहायक दस्तावेज़',
        'apply': 'आप Services सेक्शन से प्रमाणपत्र के लिए आवेदन कर सकते हैं। सही प्रमाणपत्र प्रकार चुनकर फॉर्म भरें।',
        'status': 'मैं आवेदन, शिकायत और बिल की स्थिति देखने में मदद कर सकता हूँ। यदि आपके पास GP या CMP नंबर है, तो exact tracking के लिए भेजें।',
        'bill': 'आप Services सेक्शन से बिजली, पानी और प्रॉपर्टी टैक्स बिल का भुगतान कर सकते हैं।',
        'complaint': 'आप Services सेक्शन से शिकायत दर्ज कर सकते हैं और बाद में My Complaints में ट्रैक कर सकते हैं।',
        'login': 'OTP या login समस्या के लिए login पेज पर जाएँ और जरूरत हो तो Resend OTP पर क्लिक करें।',
    },
    'mr': {
        'fallback': 'मी प्रमाणपत्र, तक्रार, बिल, अर्ज स्थिती आणि OTP/लॉगिनमध्ये मदत करू शकतो. कृपया वेगळ्या पद्धतीने विचारा.',
        'docs': 'प्रमाणपत्र अर्जासाठी आवश्यक कागदपत्रे:\n- आधार कार्ड\n- पत्ता पुरावा\n- पासपोर्ट आकाराचा फोटो\n- सहाय्यक कागदपत्रे',
        'apply': 'तुम्ही Services विभागातून प्रमाणपत्रासाठी अर्ज करू शकता. योग्य प्रमाणपत्र प्रकार निवडून फॉर्म भरा.',
        'status': 'मी अर्ज, तक्रार आणि बिल स्थिती तपासण्यात मदत करू शकतो. GP किंवा CMP नंबर असल्यास exact tracking साठी पाठवा.',
        'bill': 'तुम्ही Services विभागातून वीज, पाणी आणि मालमत्ता कर बिल भरू शकता.',
        'complaint': 'तुम्ही Services विभागातून तक्रार नोंदवू शकता आणि नंतर My Complaints मध्ये track करू शकता.',
        'login': 'OTP किंवा login समस्येसाठी login पेजवर जा आणि गरज असल्यास Resend OTP वर क्लिक करा.',
    },
}

INTENT_KEYWORDS = [
    ('income_certificate', ['income certificate', 'income proof', 'income', 'आय प्रमाणपत्र', 'उत्पन्न प्रमाणपत्र', 'उत्पन्न', 'आय', 'income kaise', 'income ka']),
    ('birth_certificate', ['birth certificate', 'birth', 'janm', 'जन्म', 'जन्म प्रमाणपत्र', 'janm certificate']),
    ('death_certificate', ['death certificate', 'death', 'mृत्यु', 'मृत्यू', 'death प्रमाणपत्र', 'death certificate apply']),
    ('complaint', ['complaint', 'grievance', 'issue', 'तक्रार', 'शिकायत', 'complaint file', 'file complaint', 'raise complaint']),
    ('electricity_bill', ['electricity bill', 'light bill', 'power bill', 'current bill', 'बिजली बिल', 'वीज बिल', 'light bill pay', 'electric bill']),
    ('water_bill', ['water bill', 'पानी बिल', 'पाणी बिल', 'water charge', 'water tax']),
    ('property_tax', ['property tax', 'property bill', 'property dues', 'मालमत्ता कर', 'घर कर', 'tax payment']),
]


def _normalize_text(value: object) -> str:
    return re.sub(r'\s+', ' ', str(value or '').strip().lower())


def _contains_any(text: str, values: Iterable[str]) -> bool:
    return any(token in text for token in values)


def _detect_language(text: str, request_language: str = '') -> str:
    if request_language in {'hi', 'mr', 'en'}:
        baseline = request_language
    else:
        baseline = 'en'

    if not text:
        return baseline

    if DEVA_RE.search(text):
        marathi_score = sum(1 for word in ['मला', 'कृपया', 'अर्ज', 'कागदपत्रे', 'तक्रार', 'पाणी', 'मालमत्ता', 'स्थिती', 'माहिती'] if word in text)
        hindi_score = sum(1 for word in ['मुझे', 'कृपया', 'दस्तावेज़', 'शिकायत', 'पानी', 'स्थिति', 'जानकारी', 'आवेदन'] if word in text)
        if marathi_score > hindi_score:
            return 'mr'
        if hindi_score > marathi_score:
            return 'hi'
        return baseline if baseline in {'hi', 'mr'} else 'hi'

    latin_text = text.lower()
    marathi_markers = ['mala', 'kasa', 'kaise', 'arj', 'kagadpatre', 'pani', 'tarakrar', 'sthiti', 'mahitI', 'mahiti', 'mahit']
    hindi_markers = ['mujhe', 'kaise', 'kyu', 'kya', 'dastavej', 'shikayat', 'stithi', 'prasn', 'apply kaise', 'kaise apply']
    if _contains_any(latin_text, marathi_markers):
        return 'mr'
    if _contains_any(latin_text, hindi_markers):
        return 'hi'
    return baseline


def _chatbot_history_key(request) -> str:
    if request.user.is_authenticated:
        return f'chatbot_history_user_{request.user.id}'
    return 'chatbot_history_anon'


def _load_history(request) -> List[Dict[str, str]]:
    history = request.session.get(_chatbot_history_key(request), [])
    if not isinstance(history, list):
        return []
    cleaned: List[Dict[str, str]] = []
    for item in history[-HISTORY_WINDOW:]:
        if isinstance(item, dict) and item.get('role') in {'user', 'assistant'}:
            cleaned.append({'role': item['role'], 'content': str(item.get('content', ''))[:800]})
    return cleaned


def _save_history(request, history: List[Dict[str, str]]) -> None:
    request.session[_chatbot_history_key(request)] = history[-HISTORY_WINDOW:]
    request.session.modified = True


def _build_suggestions(language: str, category: str = 'welcome') -> List[str]:
    language_key = language if language in SUGGESTIONS else 'en'
    return SUGGESTIONS[language_key].get(category) or SUGGESTIONS[language_key]['welcome']


def _build_service_action(action_key: str) -> Dict[str, object]:
    action = dict(SERVICE_ACTIONS[action_key])
    action['url'] = reverse(action.pop('url_name'))
    return action


def _fallback_reply(language: str) -> str:
    return HELP_COPY.get(language, HELP_COPY['en'])['fallback']


def _reference_reply(request, text: str, language: str) -> Optional[Dict[str, object]]:
    app_match = APPLICATION_RE.search(text.upper())
    if app_match:
        application_number = app_match.group(0).upper()
        qs = Application.objects.filter(application_number=application_number)
        if request.user.is_authenticated and request.user.role not in {'staff', 'admin'}:
            qs = qs.filter(applicant=request.user)
        application = qs.first()
        if application:
            reviewed_text = (
                f"Reviewed on {application.reviewed_date.strftime('%d %b %Y')}." if application.reviewed_date else 'It is currently being processed.'
            )
            detail_url = (
                reverse('admin_review_application', kwargs={'application_id': application.id})
                if request.user.is_authenticated and request.user.role in {'staff', 'admin'}
                else reverse('application_detail', kwargs={'application_id': application.id})
            )
            return {
                'reply': (
                    f"I checked that for you 😊\n\n"
                    f"- Application ID: {application.application_number}\n"
                    f"- Current status: {application.get_status_display()}\n"
                    f"- Service: {application.get_application_type_display()}\n"
                    f"- Note: {reviewed_text}\n\n"
                    f"You can open full details here: {detail_url}"
                ),
                'suggestions': _build_suggestions(language, 'status'),
                'source': 'record_lookup',
                'language': language,
            }

    complaint_match = COMPLAINT_RE.search(text.upper())
    if complaint_match:
        complaint_number = complaint_match.group(0).upper()
        qs = Complaint.objects.filter(complaint_number=complaint_number)
        if request.user.is_authenticated and request.user.role not in {'staff', 'admin'}:
            qs = qs.filter(complainant=request.user)
        complaint = qs.first()
        if complaint:
            detail_url = (
                reverse('admin_update_complaint', kwargs={'complaint_id': complaint.id})
                if request.user.is_authenticated and request.user.role in {'staff', 'admin'}
                else reverse('complaint_detail', kwargs={'complaint_id': complaint.id})
            )
            return {
                'reply': (
                    f"I found your complaint details 😊\n\n"
                    f"- Complaint ID: {complaint.complaint_number}\n"
                    f"- Current status: {complaint.get_status_display()}\n"
                    f"- Priority: {complaint.get_priority_display()}\n\n"
                    f"You can view full details here: {detail_url}"
                ),
                'suggestions': _build_suggestions(language, 'complaint'),
                'source': 'record_lookup',
                'language': language,
            }

    return None


def _detect_intent(text: str) -> Optional[Tuple[str, str]]:
    for intent_key, aliases in INTENT_KEYWORDS:
        if _contains_any(text, aliases):
            return intent_key, aliases[0]
    return None


def _build_intent_reply(request, intent_key: str, language: str, text: str) -> Dict[str, object]:
    copy = HELP_COPY.get(language, HELP_COPY['en'])
    if intent_key == 'income_certificate':
        return {
            'reply': (
                'Sure! 😊\nTo apply for an income certificate, open Services, select Income Certificate, fill in your details, upload the required documents, and submit the form.'
                if language == 'en'
                else 'ज़रूर! 😊\nआय प्रमाणपत्र के लिए Services में जाएँ, Income Certificate चुनें, विवरण भरें, दस्तावेज़ अपलोड करें, और form submit करें.'
                if language == 'hi'
                else 'नक्की! 😊\nउत्पन्न प्रमाणपत्रासाठी Services मध्ये जा, Income Certificate निवडा, माहिती भरा, कागदपत्रे अपलोड करा आणि form submit करा.'
            ),
            'action': _build_service_action('income_certificate'),
            'suggestions': _build_suggestions(language, 'certificate'),
            'source': 'intent',
            'language': language,
        }
    if intent_key == 'birth_certificate':
        return {
            'reply': (
                'Of course 😊\nOpen Services, choose Birth Certificate, enter child and parent details, upload supporting documents, and submit.'
                if language == 'en'
                else 'बिलकुल 😊\nServices खोलें, Birth Certificate चुनें, बच्चे और माता-पिता की जानकारी भरें, दस्तावेज़ अपलोड करें और submit करें.'
                if language == 'hi'
                else 'नक्कीच 😊\nServices उघडा, Birth Certificate निवडा, बालक व पालकांची माहिती भरा, कागदपत्रे अपलोड करा आणि submit करा.'
            ),
            'action': _build_service_action('birth_certificate'),
            'suggestions': _build_suggestions(language, 'certificate'),
            'source': 'intent',
            'language': language,
        }
    if intent_key == 'death_certificate':
        return {
            'reply': (
                'I can help with that 😊\nOpen Services, select Death Certificate, enter deceased and informant details, upload supporting proof, and submit.'
                if language == 'en'
                else 'मैं मदद कर सकता हूँ 😊\nServices में जाएँ, Death Certificate चुनें, deceased और informant details भरें, proofs upload करें और submit करें.'
                if language == 'hi'
                else 'मी मदत करू शकतो 😊\nServices मध्ये जा, Death Certificate निवडा, मृत व्यक्ती व informant तपशील भरा, पुरावे अपलोड करा आणि submit करा.'
            ),
            'action': _build_service_action('death_certificate'),
            'suggestions': _build_suggestions(language, 'certificate'),
            'source': 'intent',
            'language': language,
        }
    if intent_key == 'complaint':
        return {
            'reply': copy['complaint'],
            'action': _build_service_action('complaint'),
            'suggestions': _build_suggestions(language, 'complaint'),
            'source': 'intent',
            'language': language,
        }
    if intent_key == 'electricity_bill':
        return {
            'reply': copy['bill'],
            'action': _build_service_action('electricity_bill'),
            'suggestions': _build_suggestions(language, 'bill'),
            'source': 'intent',
            'language': language,
        }
    if intent_key == 'water_bill':
        return {
            'reply': copy['bill'],
            'action': _build_service_action('water_bill'),
            'suggestions': _build_suggestions(language, 'bill'),
            'source': 'intent',
            'language': language,
        }
    if intent_key == 'property_tax':
        return {
            'reply': copy['bill'],
            'action': _build_service_action('property_tax'),
            'suggestions': _build_suggestions(language, 'bill'),
            'source': 'intent',
            'language': language,
        }
    return {
        'reply': _fallback_reply(language),
        'suggestions': _build_suggestions(language, 'welcome'),
        'source': 'fallback',
        'language': language,
    }


def _build_system_prompt(language: str, request) -> str:
    request_language = language.upper()
    role = request.user.role if getattr(request.user, 'is_authenticated', False) else 'guest'
    return (
        f"You are the smart help desk assistant for the Digital Gram Panchayat Portal.\n"
        f"Respond in {request_language}. Keep the answer concise, practical, and friendly.\n"
        f"If the user mixes languages, answer in the dominant language they used.\n"
        f"Available services: birth certificate, death certificate, income certificate, electricity bill, water bill, property tax, complaint filing, application tracking, OTP/login support.\n"
        f"If the user asks for required documents, explain the documents clearly in bullets.\n"
        f"If the user asks about the portal, you may mention that dashboard and Services sections are used to apply.\n"
        f"Never invent application status or account details.\n"
        f"The current user role is: {role}.\n"
        f"If a question needs exact tracking and the user has not provided a GP/CMP number, ask for it politely."
    )


def _call_openai(prompt: str, system_prompt: str) -> Optional[str]:
    api_key = getattr(settings, 'CHATBOT_OPENAI_API_KEY', '')
    if not api_key:
        return None

    model = getattr(settings, 'CHATBOT_OPENAI_MODEL', 'gpt-4o-mini')
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.25,
        'max_tokens': 350,
    }
    data = json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(
        'https://api.openai.com/v1/chat/completions',
        data=data,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    timeout = getattr(settings, 'CHATBOT_TIMEOUT_SECONDS', 8)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode('utf-8')
    payload = json.loads(body)
    choices = payload.get('choices') or []
    if not choices:
        return None
    message = choices[0].get('message') or {}
    return str(message.get('content') or '').strip() or None


def _call_gemini(prompt: str, system_prompt: str) -> Optional[str]:
    api_key = getattr(settings, 'CHATBOT_GEMINI_API_KEY', '')
    if not api_key:
        return None

    model = getattr(settings, 'CHATBOT_GEMINI_MODEL', 'gemini-1.5-flash')
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model)}:generateContent?key={urllib.parse.quote(api_key)}'
    payload = {
        'contents': [
            {
                'role': 'user',
                'parts': [
                    {'text': f'{system_prompt}\n\nUser query:\n{prompt}'}
                ],
            }
        ],
        'generationConfig': {
            'temperature': 0.25,
            'maxOutputTokens': 350,
        },
    }
    data = json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    timeout = getattr(settings, 'CHATBOT_TIMEOUT_SECONDS', 8)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode('utf-8')
    payload = json.loads(body)
    candidates = payload.get('candidates') or []
    if not candidates:
        return None
    content = ((candidates[0].get('content') or {}).get('parts') or [])
    text = ''.join(str(part.get('text') or '') for part in content).strip()
    return text or None


def _clean_reply(text: str) -> str:
    reply = re.sub(r'\n{3,}', '\n\n', str(text or '').strip())
    return reply[:MAX_REPLY_LENGTH]


def _knowledge_reply(text: str, language: str, request) -> Optional[Dict[str, object]]:
    lowered = _normalize_text(text)
    copy = HELP_COPY.get(language, HELP_COPY['en'])

    reference_reply = _reference_reply(request, lowered, language)
    if reference_reply:
        return reference_reply

    if _contains_any(lowered, ['required documents', 'documents', 'document', 'कागदपत्र', 'दस्तावेज', 'कागदपत्रे']):
        return {
            'reply': copy['docs'],
            'suggestions': _build_suggestions(language, 'documents'),
            'source': 'intent',
            'language': language,
        }

    if _contains_any(lowered, ['how to apply', 'apply certificate', 'certificate apply', 'certificate kaise', 'certificate कसे', 'certificate कैसे', 'प्रमाणपत्र', 'प्रमाणपत्रासाठी', 'certificate']) and not _contains_any(lowered, ['income', 'birth', 'death']):
        return {
            'reply': copy['apply'],
            'suggestions': _build_suggestions(language, 'certificate'),
            'source': 'intent',
            'language': language,
        }

    if _contains_any(lowered, ['status', 'track', 'application status', 'complaint status', 'bill status', 'स्थिति', 'स्थिती']):
        return {
            'reply': copy['status'],
            'suggestions': _build_suggestions(language, 'status'),
            'source': 'intent',
            'language': language,
        }

    if _contains_any(lowered, ['pay bill', 'bill pay', 'electricity bill', 'water bill', 'property tax', 'बिल', 'बिल भुगतान', 'बिल भरणा', 'कर भरणा']):
        return {
            'reply': copy['bill'],
            'suggestions': _build_suggestions(language, 'bill'),
            'source': 'intent',
            'language': language,
        }

    if _contains_any(lowered, ['otp', 'login', 'password', 'verification', 'verification code', 'लॉगिन', 'पासवर्ड', 'ओटीपी']):
        return {
            'reply': copy['login'],
            'suggestions': _build_suggestions(language, 'welcome'),
            'source': 'intent',
            'language': language,
        }

    return None


def build_chatbot_response(request, user_message: str) -> Dict[str, object]:
    """Return a hybrid chatbot response for the shared chatbot endpoint."""
    text = _normalize_text(user_message)
    request_language = getattr(request, 'LANGUAGE_CODE', '') or getattr(getattr(request, 'language', None), 'code', '') or ''
    language = _detect_language(text, request_language)

    if not text:
        return {
            'reply': _fallback_reply(language),
            'suggestions': _build_suggestions(language),
            'source': 'fallback',
            'language': language,
            'status': 200,
        }

    if not getattr(settings, 'CHATBOT_ENABLED', True):
        knowledge = _knowledge_reply(text, language, request)
        if knowledge:
            return {**knowledge, 'status': 200}
        return {
            'reply': _fallback_reply(language),
            'suggestions': _build_suggestions(language),
            'source': 'fallback',
            'language': language,
            'status': 200,
        }

    history = _load_history(request)

    knowledge = _knowledge_reply(text, language, request)
    if knowledge:
        history.append({'role': 'user', 'content': user_message})
        history.append({'role': 'assistant', 'content': knowledge['reply']})
        _save_history(request, history)
        return {**knowledge, 'status': 200}

    prompt = (
        f"Conversation history:\n{json.dumps(history[-HISTORY_WINDOW:], ensure_ascii=False)}\n\n"
        f"User message:\n{user_message}\n\n"
        f"Respond in the same language as the user. Keep the answer concise, useful, and portal-specific."
    )
    system_prompt = _build_system_prompt(language, request)

    reply_text = None
    provider = getattr(settings, 'CHATBOT_PROVIDER', 'openai')
    try:
        if provider == 'gemini':
            reply_text = _call_gemini(prompt, system_prompt)
        else:
            reply_text = _call_openai(prompt, system_prompt)
            if not reply_text:
                reply_text = _call_gemini(prompt, system_prompt)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
        reply_text = None

    if reply_text:
        cleaned_reply = _clean_reply(reply_text)
        history.append({'role': 'user', 'content': user_message})
        history.append({'role': 'assistant', 'content': cleaned_reply})
        _save_history(request, history)
        return {
            'reply': cleaned_reply,
            'suggestions': _build_suggestions(language),
            'source': 'ai',
            'language': language,
            'status': 200,
        }

    fallback_reply = _fallback_reply(language)
    history.append({'role': 'user', 'content': user_message})
    history.append({'role': 'assistant', 'content': fallback_reply})
    _save_history(request, history)
    return {
        'reply': fallback_reply,
        'suggestions': _build_suggestions(language),
        'source': 'fallback',
        'language': language,
        'status': 200,
    }