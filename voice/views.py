from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from groq import Groq
import os
from django.conf import settings
import json
import tempfile
import subprocess
from pathlib import Path

# Initialize Groq client
groq_client = None
whisper_model = None

def get_whisper_model():
    """Initialize Whisper model lazily"""
    global whisper_model
    if whisper_model is None:
        os.environ['OPENBLAS_NUM_THREADS'] = '1'
        from faster_whisper import WhisperModel
        # Use 'base' model - good balance of speed and accuracy
        # For better accuracy, use 'small' or 'medium'
        whisper_model = WhisperModel(
            "base", 
            device="cpu", 
            compute_type="int8",
            download_root=None,  # Use default cache directory
            num_workers=1
        )
    return whisper_model

def get_groq_client():
    """Initialize Groq client lazily"""
    global groq_client
    if groq_client is None:
        api_key = settings.GROQ_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_KEY not configured in settings")
        groq_client = Groq(api_key=api_key)
    return groq_client

def convert_audio_to_wav(input_path, output_path):
    """
    Convert audio file to WAV format using ffmpeg
    This ensures compatibility with faster-whisper
    """
    try:
        # Check if ffmpeg is available
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        
        # Convert to WAV: mono, 16kHz sample rate (optimal for Whisper)
        command = [
            'ffmpeg',
            '-i', input_path,
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',      # Mono audio
            '-c:a', 'pcm_s16le',  # PCM 16-bit encoding
            '-y',            # Overwrite output file
            output_path
        ]
        
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg conversion error: {e.stderr.decode()}")
        return False
    except FileNotFoundError:
        print("FFmpeg not found. Please install ffmpeg: sudo apt-get install ffmpeg")
        return False

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transcribe_audio(request):
    """
    Transcription using faster-whisper with proper audio conversion
    """
    temp_audio_path = None
    temp_wav_path = None
    
    try:
        audio_file = request.FILES.get('audio')
        
        if not audio_file:
            return Response({
                'success': False,
                'message': 'No audio file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"Received audio file: {audio_file.name}, size: {audio_file.size} bytes")
        
        # Check file size (should be > 0)
        if audio_file.size == 0:
            return Response({
                'success': False,
                'message': 'Audio file is empty'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save original audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.m4a') as temp_audio:
            for chunk in audio_file.chunks():
                temp_audio.write(chunk)
            temp_audio_path = temp_audio.name
        
        print(f"Saved audio to: {temp_audio_path}")
        
        # Convert to WAV for better compatibility
        temp_wav_path = temp_audio_path.replace('.m4a', '.wav')
        
        conversion_success = convert_audio_to_wav(temp_audio_path, temp_wav_path)
        
        # Use converted WAV if available, otherwise try original
        audio_path_to_transcribe = temp_wav_path if conversion_success else temp_audio_path
        
        print(f"Transcribing from: {audio_path_to_transcribe}")
        
        # Transcribe using local Whisper model
        model = get_whisper_model()
        
        segments, info = model.transcribe(
            audio_path_to_transcribe,
            language="en",
            beam_size=5,
            vad_filter=True,  # Voice activity detection
            vad_parameters=dict(
                min_silence_duration_ms=500,  # Minimum silence duration
                threshold=0.5  # VAD threshold
            ),
            condition_on_previous_text=False,  # Don't condition on previous text
            temperature=0.0,  # Deterministic output
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6
        )
        
        # Collect all segments
        transcript_segments = list(segments)
        
        # Combine all segments into full transcript
        transcript_text = " ".join([segment.text.strip() for segment in transcript_segments])
        
        print(f"Transcription result: '{transcript_text}'")
        print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
        
        # Check if transcript is empty
        if not transcript_text.strip():
            return Response({
                'success': False,
                'message': 'No speech detected in audio'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'data': {
                'text': transcript_text.strip(),
                'language': info.language,
                'language_probability': info.language_probability,
                'duration': info.duration
            }
        })
        
    except Exception as e:
        print(f"Transcription error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return Response({
            'success': False,
            'message': f'Transcription failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    finally:
        # Clean up temporary files
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except Exception as e:
                print(f"Failed to remove temp audio: {e}")
        
        if temp_wav_path and os.path.exists(temp_wav_path):
            try:
                os.remove(temp_wav_path)
            except Exception as e:
                print(f"Failed to remove temp wav: {e}")

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_voice_command(request):
    """
    AI Processing using Llama 3.1 via Groq API
    """
    try:
        user = request.user
        text = request.data.get('text', '')
        user_context = request.data.get('userContext', {})
        conversation_history = request.data.get('conversationHistory', [])
        
        if not text:
            return Response({
                'success': False,
                'message': 'No text provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"Processing voice command: '{text}'")
        
        # Get comprehensive user context
        from accounts.models import Profile
        
        # Get user profile and wallet info
        try:
            profile = user.profile
            wallet_balance = float(profile.wallet_balance or 0)
            wallet_points = profile.wallet_points or 0
        except Profile.DoesNotExist:
            wallet_balance = 0
            wallet_points = 0
        
        # Get user's order statistics
        total_orders = user.client_orders.count()
        completed_orders = user.client_orders.filter(status='completed').count()
        pending_orders = user.client_orders.filter(status='pending').count()
        in_progress_orders = user.client_orders.filter(status__in=['in_progress', 'assigned']).count()
        
        # Get recent orders with details
        recent_orders = list(user.client_orders.order_by('-created_at')[:5].values(
            'id', 'title', 'order_type__name', 'status', 'price', 'created_at'
        ))
        # Rename fields for consistency
        for order in recent_orders:
            order['service_type'] = order.get('order_type__name') or 'Unknown'
            order['total_amount'] = float(order.get('price') or 0)
            order.pop('order_type__name', None)
            order.pop('price', None)
        
        # Build comprehensive system prompt
        system_prompt = f"""You are Fagi, a helpful and friendly female voice assistant for Fagi Errands - a comprehensive task management and errand service app. You assist customers throughout the entire app experience.

USER PROFILE:
- Name: {user.first_name} {user.last_name}
- Email: {user.email}
- User Type: {user.user_type}
- Wallet Balance: KSh {wallet_balance:.2f}
- Reward Points: {wallet_points} points
- Total Orders: {total_orders}
- Completed Orders: {completed_orders}
- Pending Orders: {pending_orders}
- Active Orders: {in_progress_orders}
- Recent Orders: {json.dumps(recent_orders, default=str)}

AVAILABLE SERVICES:
1. Shopping - Groceries & Essentials (Purchase and delivery of groceries, goods, or other items)
2. Pickup & Delivery - Parcel Delivery & Pickup Services (Pickup and delivery service for packages, documents, or other items)
3. Cargo Transport - Heavy Cargo & Freight Services (Transport of larger items or cargo requiring special handling)
4. Cheque Banking - Cheque Deposit Services (Assistance with banking tasks such as cheque deposits)
5. Home Maintenance - Professional Home Maintenance Services (Home repair, maintenance including Plumbing, Electrical Works, Landscaping)

NAVIGATION OPTIONS:
Main Tabs:
- home: Main dashboard
- orders: View all orders
- notifications: View notifications
- referrals: Referral program and rewards
- profile: User profile and settings
- shop: Shopping marketplace

Screens:
- order-details: View order details (requires orderId)
- order-tracking: Track order location (requires orderId)
- payment: Payment screen (requires orderId and amount)
- map: Map view for order tracking
- settings: App settings
- wallet: Wallet balance and transactions
- edit-profile: Edit user profile
- saved-addresses: Manage saved addresses
- chatbot: Text chatbot support
- order-history: Complete order history
- payment-methods: Manage payment methods
- help-support: Help and support center

YOUR CAPABILITIES:
1. Navigation: Help users navigate to any screen, tab, or service
2. Order Information: Answer questions about order status, tracking, history, pricing
3. Order Creation: Help users create orders by guiding them to order creation screens and collecting information through conversation
4. Service Guidance: Explain services, help create orders, provide pricing information
5. Account Help: Check wallet balance, view profile info, manage settings
6. General Support: Answer app questions, provide help, explain features
7. Conversational: Have natural conversations, be friendly and empathetic

RESPONSE FORMAT:
Always respond with ONLY valid JSON in this exact format:
{{
  "message": "Your friendly spoken response (2-3 sentences max, conversational)",
  "action": {{
    "type": "navigate|tab|service|none",
    "params": {{}}
  }}
}}

ACTION TYPES:
- "tab": Switch to a main tab (home, orders, notifications, referrals, profile, shop)
- "navigate": Navigate to a specific screen (order-details, order-tracking, wallet, settings, etc.)
- "service": Open a service creation screen (Shopping, Pickup & Delivery, Cargo Transport, Cheque Banking, Home Maintenance)
- "create_order": Start creating a new order with specified service and basic details
- "none": Just answer the question without navigation

ORDER CREATION:
When users want to place orders, extract order information from their voice and pre-fill the form automatically.

EXTRACTING ORDER INFORMATION:
- Items: Look for quantities and items (e.g., "2 kilos rice", "1 liter milk", "3 bottles water")
- Addresses: Extract delivery addresses, pickup addresses, locations (e.g., "Westlands", "Nairobi CBD", "Kilimani")
- Quantities: Parse numbers with units (kilos, liters, pieces, bags, etc.)
- Service types: Identify which service based on keywords (groceries/shopping, pickup/delivery, cargo, maintenance, banking)

When creating orders, extract and structure the following information:
- Shopping: items (with quantities), delivery_address, preferred_outlet (optional), description
- Pickup & Delivery: pickup_address, delivery_address, description
- Cargo: pickup_address, delivery_address, cargo items, weight/dimensions
- Home Maintenance: service type, address, description, scheduled date/time

RESPONSE FORMAT FOR ORDER CREATION:
When order details are provided, use this format:
{{
  "message": "I'll create that order for you! Opening the form with your details pre-filled.",
  "action": {{
    "type": "create_order",
    "params": {{
      "service": "Shopping",
      "orderData": {{
        "items": [{{"name": "rice", "quantity": 2, "unit": "kilos"}}, {{"name": "milk", "quantity": 1, "unit": "liters"}}],
        "delivery_address": "Westlands",
        "description": "Groceries order"
      }}
    }}
  }}
}}

EXAMPLES:
- "show my orders" → {{"message": "Opening your orders now. You have {total_orders} total orders.", "action": {{"type": "tab", "params": {{"tab": "orders"}}}}}}
- "what's my wallet balance" → {{"message": "Your wallet balance is KSh {wallet_balance:.2f} and you have {wallet_points} reward points.", "action": {{"type": "none"}}}}
- "I need groceries" → {{"message": "Perfect! I'll help you place a shopping order. Opening the shopping service for you.", "action": {{"type": "service", "params": {{"service": "Shopping"}}}}}}
- "place an order for groceries" → {{"message": "Great! I'll help you create a shopping order. Let me open the shopping service where you can add items and delivery details.", "action": {{"type": "service", "params": {{"service": "Shopping"}}}}}}
- "order groceries for delivery to Westlands" → {{"message": "I'll create a shopping order for delivery to Westlands. Opening the form with that address pre-filled.", "action": {{"type": "create_order", "params": {{"service": "Shopping", "orderData": {{"delivery_address": "Westlands"}}}}}}}}
- "order 2 kilos of rice, 1 liter of milk, and bread for delivery to Westlands" → {{"message": "Perfect! I'll create your shopping order with 2 kilos of rice, 1 liter of milk, and bread for delivery to Westlands.", "action": {{"type": "create_order", "params": {{"service": "Shopping", "orderData": {{"items": [{{"name": "rice", "quantity": 2, "unit": "kilos"}}, {{"name": "milk", "quantity": 1, "unit": "liters"}}, {{"name": "bread", "quantity": 1}}], "delivery_address": "Westlands", "description": "Groceries: rice, milk, bread"}}}}}}}}
- "pickup a package from Kilimani and deliver it to Westlands" → {{"message": "I'll create a pickup and delivery order from Kilimani to Westlands for you.", "action": {{"type": "create_order", "params": {{"service": "Pickup & Delivery", "orderData": {{"pickup_address": "Kilimani", "delivery_address": "Westlands", "description": "Package pickup and delivery"}}}}}}}}
- "create a pickup order" → {{"message": "I'll help you create a pickup and delivery order. Opening that service for you.", "action": {{"type": "service", "params": {{"service": "Pickup & Delivery"}}}}}}
- "I need cargo transport" → {{"message": "I'll help you arrange cargo transport. Opening the cargo service for you.", "action": {{"type": "service", "params": {{"service": "Cargo Transport"}}}}}}
- "book home maintenance" → {{"message": "I'll help you book home maintenance services. Opening that service for you.", "action": {{"type": "service", "params": {{"service": "Home Maintenance"}}}}}}
- "track my order" → {{"message": "I'll help you track your order. Opening order tracking now.", "action": {{"type": "navigate", "params": {{"screen": "order-tracking"}}}}}}
- "how many orders do I have" → {{"message": "You have {total_orders} total orders. {completed_orders} completed, {pending_orders} pending, and {in_progress_orders} currently in progress.", "action": {{"type": "none"}}}}
- "open my wallet" → {{"message": "Opening your wallet now. Your balance is KSh {wallet_balance:.2f}.", "action": {{"type": "navigate", "params": {{"screen": "wallet"}}}}}}
- "what services do you offer" → {{"message": "We offer 5 main services: Shopping for groceries, Pickup & Delivery for parcels, Cargo Transport for heavy items, Cheque Banking for deposits, and Home Maintenance for repairs. Which one interests you?", "action": {{"type": "none"}}}}
- "go to profile" → {{"message": "Opening your profile now.", "action": {{"type": "tab", "params": {{"tab": "profile"}}}}}}
- "I want to place an order" → {{"message": "I'd be happy to help you place an order! We offer Shopping, Pickup & Delivery, Cargo Transport, Cheque Banking, and Home Maintenance. Which service would you like?", "action": {{"type": "none"}}}}

CONVERSATION STYLE:
- Be warm, friendly, and conversational
- Use the user's name when appropriate ({user.first_name})
- Show empathy and understanding
- Provide helpful information proactively
- Keep responses concise for voice (2-3 sentences max)
- If user asks about something you can't do, suggest alternatives

Current user query: {text}

Remember: Respond ONLY with valid JSON! Never include any text outside the JSON object."""

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (last 6 messages)
        for msg in conversation_history[-6:]:
            messages.append({
                "role": msg.get('role', 'user'),
                "content": msg.get('content', '')
            })
        
        # Add current message
        messages.append({"role": "user", "content": text})
        
        # Call Groq API
        client = get_groq_client()
        # Get model from settings (defaults to llama-3.1-8b-instant)
        model_name = getattr(settings, 'GROQ_MODEL', 'llama-3.1-8b-instant')
        
        # List of available models to try in order
        available_models = [
            model_name,  # Try configured model first
            'llama-3.1-8b-instant',  # Most common/default
            'llama-3.3-70b-versatile',  # Alternative 70b model
            'mixtral-8x7b-32768',  # Alternative model
        ]
        
        # Try models in order until one works
        chat_completion = None
        last_error = None
        for model_to_try in available_models:
            try:
                print(f"Trying model: {model_to_try}")
                chat_completion = client.chat.completions.create(
                    model=model_to_try,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=400,  # Increased for more comprehensive responses
                    response_format={"type": "json_object"}
                )
                print(f"Successfully used model: {model_to_try}")
                break  # Success, exit the loop
            except Exception as e:
                last_error = e
                print(f"Error with {model_to_try}: {e}")
                continue
        
        # If all models failed, raise the last error
        if chat_completion is None:
            raise Exception(f"All models failed. Last error: {last_error}")
        
        # Parse response
        llama_response = chat_completion.choices[0].message.content
        print(f"Llama response: {llama_response}")
        
        parsed_response = json.loads(llama_response)
        
        # Ensure proper structure
        if 'message' not in parsed_response:
            parsed_response['message'] = "I'm here to help! What would you like to do?"
        
        if 'action' not in parsed_response:
            parsed_response['action'] = None
        
        return Response({
            'success': True,
            'data': parsed_response
        })
        
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {str(e)}")
        print(f"Raw response: {llama_response if 'llama_response' in locals() else 'N/A'}")
        
        return Response({
            'success': True,
            'data': {
                'message': "I'm here to help! What would you like to do?",
                'action': None
            }
        })
        
    except Exception as e:
        print(f"Voice command processing error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return Response({
            'success': False,
            'message': f'Failed to process command: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_voice_context(request):
    """Get contextual information for voice assistant"""
    try:
        user = request.user
        from accounts.models import Profile
        
        # Get user profile and wallet info
        try:
            profile = user.profile
            wallet_balance = float(profile.wallet_balance or 0)
            wallet_points = profile.wallet_points or 0
        except Profile.DoesNotExist:
            wallet_balance = 0
            wallet_points = 0
        
        # Get user stats
        total_orders = user.client_orders.count()
        completed_orders = user.client_orders.filter(status='completed').count()
        pending_orders = user.client_orders.filter(status='pending').count()
        active_orders = user.client_orders.filter(
            status__in=['pending', 'in_progress', 'assigned']
        ).count()
        
        # Get recent orders
        recent_orders = list(user.client_orders.order_by('-created_at')[:5].values(
            'id', 'title', 'order_type__name', 'status', 'price', 'created_at'
        ))
        # Rename fields for consistency
        for order in recent_orders:
            order['service_type'] = order.get('order_type__name') or 'Unknown'
            order['total_amount'] = float(order.get('price') or 0)
            order.pop('order_type__name', None)
            order.pop('price', None)
        
        context = {
            'user_info': {
                'name': f"{user.first_name} {user.last_name}",
                'email': user.email,
                'user_type': user.user_type,
            },
            'wallet': {
                'balance': wallet_balance,
                'points': wallet_points,
            },
            'stats': {
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'pending_orders': pending_orders,
                'active_orders': active_orders,
            },
            'recent_orders': recent_orders,
        }
        
        return Response({
            'success': True,
            'data': context
        })
        
    except Exception as e:
        print(f"Get voice context error: {str(e)}")
        return Response({
            'success': False,
            'message': f'Failed to get context: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)