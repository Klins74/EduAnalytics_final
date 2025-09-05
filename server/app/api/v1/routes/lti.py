"""LTI 1.3 API routes for OIDC login, Deep Linking, and content delivery."""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.lti_service import lti_service, ContentItem, LTILaunchData, DeepLinkingRequest
from app.services.lti_ags_service import get_lti_ags_service, LineItem, Score

router = APIRouter(prefix="/lti", tags=["LTI 1.3"])


class OIDCLoginRequest(BaseModel):
    """OIDC login request model."""
    iss: str
    login_hint: str
    target_link_uri: str
    client_id: str
    lti_deployment_id: Optional[str] = None
    lti_message_hint: Optional[str] = None


class DeepLinkingContentRequest(BaseModel):
    """Deep Linking content selection request."""
    selected_items: List[str]
    return_url: str


class GradeSubmissionRequest(BaseModel):
    """Grade submission request."""
    platform_id: str
    context_id: str
    assignment_id: int
    student_id: int
    score: float
    max_score: float
    comment: Optional[str] = None


class BulkGradeSyncRequest(BaseModel):
    """Bulk grade sync request."""
    platform_id: str
    context_id: str
    assignment_id: int


class LineItemRequest(BaseModel):
    """Line item creation request."""
    platform_id: str
    context_id: str
    label: str
    score_maximum: float
    resource_id: Optional[str] = None
    resource_link_id: Optional[str] = None


@router.get("/jwks", summary="Get JSON Web Key Set")
async def get_jwks() -> Dict[str, Any]:
    """Get JWKS for platform verification of our signatures."""
    return lti_service.get_jwks()


@router.post("/oidc/login", summary="Handle OIDC login initiation")
async def oidc_login(request: Request) -> RedirectResponse:
    """Handle OIDC login initiation from LTI platform."""
    try:
        # Get form data
        form_data = await request.form()
        request_data = dict(form_data)
        
        # Handle OIDC login
        auth_url = await lti_service.handle_oidc_login(request_data)
        
        # Redirect to platform authorization endpoint
        return RedirectResponse(url=auth_url, status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OIDC login failed: {str(e)}"
        )


@router.post("/launch", summary="Handle LTI launch")
async def lti_launch(
    request: Request,
    id_token: str = Form(...),
    state: str = Form(...)
) -> HTMLResponse:
    """Handle LTI launch with ID token."""
    try:
        # Handle LTI launch
        launch_data = await lti_service.handle_lti_launch(id_token, state)
        
        # Check message type and route accordingly
        if launch_data.message_type == "LtiResourceLinkRequest":
            # Regular resource link launch
            return await _handle_resource_link_launch(launch_data)
        elif launch_data.message_type == "LtiDeepLinkingRequest":
            # Deep Linking request
            return await _handle_deep_linking_request(launch_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported message type: {launch_data.message_type}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LTI launch failed: {str(e)}"
        )


async def _handle_resource_link_launch(launch_data: LTILaunchData) -> HTMLResponse:
    """Handle resource link launch."""
    # Determine content type from custom parameters
    content_type = launch_data.custom_params.get('content_type', 'default')
    
    if content_type == 'analytics':
        content_url = "/lti/content/analytics"
    elif content_type == 'ai_assistant':
        content_url = "/lti/content/ai-assistant"
    elif content_type == 'quiz':
        content_url = "/lti/content/quiz"
    else:
        content_url = "/lti/content/default"
    
    # Generate launch HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>EduAnalytics - {launch_data.context_title or 'Course Content'}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                border-bottom: 1px solid #ddd;
                padding-bottom: 15px;
                margin-bottom: 20px;
            }}
            .loading {{
                text-align: center;
                padding: 50px;
            }}
            iframe {{
                width: 100%;
                height: 600px;
                border: none;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>EduAnalytics</h1>
                <p>Course: {launch_data.context_title or 'Unknown'}</p>
                <p>User: {launch_data.user_name or 'Unknown'}</p>
            </div>
            <div class="loading">
                <p>Loading content...</p>
            </div>
            <iframe src="{content_url}?launch_id={launch_data.resource_link_id}" 
                    onload="document.querySelector('.loading').style.display='none'">
            </iframe>
        </div>
        
        <script>
            // Handle iframe communication
            window.addEventListener('message', function(event) {{
                if (event.data.type === 'resize') {{
                    const iframe = document.querySelector('iframe');
                    if (iframe && event.data.height) {{
                        iframe.style.height = event.data.height + 'px';
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


async def _handle_deep_linking_request(launch_data: LTILaunchData) -> HTMLResponse:
    """Handle Deep Linking request."""
    try:
        # Parse Deep Linking request
        dl_request = await lti_service.handle_deep_linking_request(launch_data)
        
        # Get available content items
        content_items = await lti_service.get_available_content_items(launch_data.context_id)
        
        # Generate Deep Linking selection HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>EduAnalytics - Select Content</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                }}
                .content-item {{
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 15px;
                    margin-bottom: 15px;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }}
                .content-item:hover {{
                    background-color: #f9f9f9;
                }}
                .content-item.selected {{
                    background-color: #e3f2fd;
                    border-color: #2196f3;
                }}
                .content-title {{
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                .content-description {{
                    color: #666;
                    margin-bottom: 10px;
                }}
                .content-features {{
                    font-size: 12px;
                    color: #888;
                }}
                .actions {{
                    text-align: center;
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                }}
                button {{
                    background-color: #2196f3;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                    margin: 0 5px;
                }}
                button:hover {{
                    background-color: #1976d2;
                }}
                button:disabled {{
                    background-color: #ccc;
                    cursor: not-allowed;
                }}
                .cancel-btn {{
                    background-color: #666;
                }}
                .cancel-btn:hover {{
                    background-color: #555;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Select EduAnalytics Content</h1>
                    <p>Choose the tools and resources you want to add to your course.</p>
                </div>
                
                <form id="contentForm">
                    <div id="contentItems">
        """
        
        # Add content items
        for i, item in enumerate(content_items):
            features = item.custom.get('features', []) if item.custom else []
            features_text = ', '.join(features) if features else ''
            
            html_content += f"""
                        <div class="content-item" data-item-id="{i}" onclick="toggleItem(this)">
                            <div class="content-title">{item.title}</div>
                            <div class="content-description">{item.text or ''}</div>
                            {f'<div class="content-features">Features: {features_text}</div>' if features_text else ''}
                            <input type="checkbox" name="selected_items" value="{i}" style="display: none;">
                        </div>
            """
        
        # Add form actions
        return_url = dl_request.deep_linking_settings.get('deep_link_return_url', '')
        
        html_content += f"""
                    </div>
                    
                    <div class="actions">
                        <button type="button" onclick="submitSelection()" id="submitBtn" disabled>
                            Add Selected Content
                        </button>
                        <button type="button" class="cancel-btn" onclick="cancelSelection()">
                            Cancel
                        </button>
                    </div>
                    
                    <input type="hidden" name="return_url" value="{return_url}">
                    <input type="hidden" name="platform_id" value="{launch_data.deployment_id}">
                    <input type="hidden" name="deployment_id" value="{launch_data.deployment_id}">
                </form>
            </div>
            
            <script>
                let selectedItems = new Set();
                
                function toggleItem(element) {{
                    const itemId = element.dataset.itemId;
                    const checkbox = element.querySelector('input[type="checkbox"]');
                    
                    if (selectedItems.has(itemId)) {{
                        selectedItems.delete(itemId);
                        element.classList.remove('selected');
                        checkbox.checked = false;
                    }} else {{
                        selectedItems.add(itemId);
                        element.classList.add('selected');
                        checkbox.checked = true;
                    }}
                    
                    document.getElementById('submitBtn').disabled = selectedItems.size === 0;
                }}
                
                async function submitSelection() {{
                    const form = document.getElementById('contentForm');
                    const formData = new FormData(form);
                    
                    try {{
                        const response = await fetch('/api/lti/deep-linking/response', {{
                            method: 'POST',
                            body: formData
                        }});
                        
                        if (response.ok) {{
                            const result = await response.text();
                            document.body.innerHTML = result;
                        }} else {{
                            alert('Error submitting selection. Please try again.');
                        }}
                    }} catch (error) {{
                        alert('Error submitting selection. Please try again.');
                    }}
                }}
                
                function cancelSelection() {{
                    const returnUrl = document.querySelector('input[name="return_url"]').value;
                    if (returnUrl) {{
                        window.location.href = returnUrl;
                    }} else {{
                        window.close();
                    }}
                }}
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deep Linking request failed: {str(e)}"
        )


@router.post("/deep-linking/response", summary="Handle Deep Linking response")
async def deep_linking_response(request: Request) -> HTMLResponse:
    """Handle Deep Linking content selection response."""
    try:
        form_data = await request.form()
        
        # Extract form data
        selected_items = form_data.getlist('selected_items')
        return_url = form_data.get('return_url')
        platform_id = form_data.get('platform_id')
        deployment_id = form_data.get('deployment_id')
        
        if not selected_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No content items selected"
            )
        
        # Get available content items
        available_items = await lti_service.get_available_content_items()
        
        # Build selected content items
        content_items = []
        for item_index in selected_items:
            try:
                index = int(item_index)
                if 0 <= index < len(available_items):
                    content_items.append(available_items[index])
            except (ValueError, IndexError):
                continue
        
        if not content_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid content item selection"
            )
        
        # Create Deep Linking response JWT
        jwt_token = await lti_service.create_deep_linking_response(
            platform_id, deployment_id, content_items, return_url
        )
        
        # Generate response HTML with auto-submit form
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Submitting Content Selection...</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 50px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    display: inline-block;
                }}
                .spinner {{
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #2196f3;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Submitting Content Selection</h2>
                <div class="spinner"></div>
                <p>Please wait while we add the selected content to your course...</p>
            </div>
            
            <form id="responseForm" action="{return_url}" method="post" style="display: none;">
                <input type="hidden" name="JWT" value="{jwt_token}">
            </form>
            
            <script>
                // Auto-submit the form
                setTimeout(function() {{
                    document.getElementById('responseForm').submit();
                }}, 1000);
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deep Linking response failed: {str(e)}"
        )


@router.get("/content/analytics", summary="Analytics content iframe")
async def analytics_content(
    launch_id: Optional[str] = Query(None),
    request: Request = None
) -> HTMLResponse:
    """Serve analytics content in iframe."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Course Analytics</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #fff;
            }
            .analytics-dashboard {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
            }
            .metric-card {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
            }
            .metric-value {
                font-size: 2em;
                font-weight: bold;
                color: #2196f3;
                margin-bottom: 10px;
            }
            .metric-label {
                color: #666;
                font-size: 14px;
            }
            .chart-placeholder {
                height: 200px;
                background: linear-gradient(45deg, #f0f0f0 25%, transparent 25%),
                           linear-gradient(-45deg, #f0f0f0 25%, transparent 25%),
                           linear-gradient(45deg, transparent 75%, #f0f0f0 75%),
                           linear-gradient(-45deg, transparent 75%, #f0f0f0 75%);
                background-size: 20px 20px;
                background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
                border-radius: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #666;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <h1>Course Analytics Dashboard</h1>
        <p>Real-time insights into student engagement and performance.</p>
        
        <div class="analytics-dashboard">
            <div class="metric-card">
                <div class="metric-value">87%</div>
                <div class="metric-label">Average Grade</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">156</div>
                <div class="metric-label">Active Students</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">23</div>
                <div class="metric-label">Assignments</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">94%</div>
                <div class="metric-label">Completion Rate</div>
            </div>
        </div>
        
        <div class="chart-placeholder">
            📊 Interactive Charts Would Load Here
        </div>
        
        <script>
            // Notify parent of content height
            function notifyParent() {
                if (window.parent) {
                    window.parent.postMessage({
                        type: 'resize',
                        height: document.body.scrollHeight
                    }, '*');
                }
            }
            
            window.addEventListener('load', notifyParent);
            window.addEventListener('resize', notifyParent);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@router.get("/content/ai-assistant", summary="AI Assistant content iframe")
async def ai_assistant_content(
    launch_id: Optional[str] = Query(None)
) -> HTMLResponse:
    """Serve AI assistant content in iframe."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Study Assistant</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #fff;
            }
            .chat-container {
                max-width: 600px;
                margin: 0 auto;
                border: 1px solid #ddd;
                border-radius: 8px;
                height: 400px;
                display: flex;
                flex-direction: column;
            }
            .chat-messages {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                background-color: #f9f9f9;
            }
            .message {
                margin-bottom: 15px;
                padding: 10px;
                border-radius: 8px;
                max-width: 80%;
            }
            .message.ai {
                background-color: #e3f2fd;
                margin-right: auto;
            }
            .message.user {
                background-color: #f3e5f5;
                margin-left: auto;
            }
            .chat-input {
                display: flex;
                padding: 15px;
                border-top: 1px solid #ddd;
                background-color: white;
            }
            .chat-input input {
                flex: 1;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-right: 10px;
            }
            .chat-input button {
                padding: 10px 20px;
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            .features {
                margin-bottom: 20px;
            }
            .feature-tag {
                display: inline-block;
                background-color: #e0e0e0;
                padding: 5px 10px;
                border-radius: 12px;
                font-size: 12px;
                margin: 2px;
            }
        </style>
    </head>
    <body>
        <h1>🤖 AI Study Assistant</h1>
        <p>Get personalized help with your coursework and study planning.</p>
        
        <div class="features">
            <span class="feature-tag">📚 Content Questions</span>
            <span class="feature-tag">📝 Study Plans</span>
            <span class="feature-tag">💡 Recommendations</span>
            <span class="feature-tag">🎯 Practice Problems</span>
        </div>
        
        <div class="chat-container">
            <div class="chat-messages" id="chatMessages">
                <div class="message ai">
                    👋 Hello! I'm your AI study assistant. I can help you with:
                    <br>• Understanding course concepts
                    <br>• Creating study schedules
                    <br>• Practice questions and explanations
                    <br>• Assignment guidance
                    <br><br>What would you like to work on today?
                </div>
            </div>
            <div class="chat-input">
                <input type="text" id="messageInput" placeholder="Ask me anything about your course..." 
                       onkeypress="if(event.key==='Enter') sendMessage()">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
        
        <script>
            function sendMessage() {
                const input = document.getElementById('messageInput');
                const messages = document.getElementById('chatMessages');
                
                if (input.value.trim()) {
                    // Add user message
                    const userMsg = document.createElement('div');
                    userMsg.className = 'message user';
                    userMsg.textContent = input.value;
                    messages.appendChild(userMsg);
                    
                    // Simulate AI response
                    setTimeout(() => {
                        const aiMsg = document.createElement('div');
                        aiMsg.className = 'message ai';
                        aiMsg.innerHTML = `🤔 That's a great question! In a real implementation, I would analyze your question "${input.value}" and provide personalized assistance based on your course content and learning progress.`;
                        messages.appendChild(aiMsg);
                        messages.scrollTop = messages.scrollHeight;
                        notifyParent();
                    }, 1000);
                    
                    input.value = '';
                    messages.scrollTop = messages.scrollHeight;
                    notifyParent();
                }
            }
            
            function notifyParent() {
                if (window.parent) {
                    window.parent.postMessage({
                        type: 'resize',
                        height: document.body.scrollHeight
                    }, '*');
                }
            }
            
            window.addEventListener('load', notifyParent);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@router.get("/content/quiz", summary="Quiz Engine content iframe")
async def quiz_content(
    launch_id: Optional[str] = Query(None)
) -> HTMLResponse:
    """Serve quiz engine content in iframe."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Interactive Quiz Engine</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #fff;
            }
            .quiz-container {
                max-width: 700px;
                margin: 0 auto;
            }
            .question-card {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .question {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 15px;
            }
            .option {
                display: block;
                margin: 10px 0;
                padding: 10px;
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            .option:hover {
                background-color: #f0f0f0;
            }
            .option.selected {
                background-color: #e3f2fd;
                border-color: #2196f3;
            }
            .quiz-progress {
                background: #f0f0f0;
                height: 8px;
                border-radius: 4px;
                margin-bottom: 20px;
            }
            .progress-bar {
                background: #2196f3;
                height: 100%;
                border-radius: 4px;
                width: 33%;
                transition: width 0.3s;
            }
            .quiz-actions {
                text-align: center;
                margin-top: 20px;
            }
            button {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                margin: 0 5px;
            }
            button:hover {
                background-color: #1976d2;
            }
            button:disabled {
                background-color: #ccc;
                cursor: not-allowed;
            }
        </style>
    </head>
    <body>
        <h1>📝 Interactive Quiz Engine</h1>
        <p>Adaptive quizzes with instant feedback and detailed analytics.</p>
        
        <div class="quiz-progress">
            <div class="progress-bar" id="progressBar"></div>
        </div>
        
        <div class="quiz-container">
            <div class="question-card">
                <div class="question" id="questionText">
                    What is the primary purpose of formative assessment in education?
                </div>
                <div class="options" id="optionsContainer">
                    <label class="option" onclick="selectOption(this, 'a')">
                        <input type="radio" name="answer" value="a" style="display: none;">
                        A) To assign final grades to students
                    </label>
                    <label class="option" onclick="selectOption(this, 'b')">
                        <input type="radio" name="answer" value="b" style="display: none;">
                        B) To provide ongoing feedback for learning improvement
                    </label>
                    <label class="option" onclick="selectOption(this, 'c')">
                        <input type="radio" name="answer" value="c" style="display: none;">
                        C) To rank students against each other
                    </label>
                    <label class="option" onclick="selectOption(this, 'd')">
                        <input type="radio" name="answer" value="d" style="display: none;">
                        D) To fulfill administrative requirements
                    </label>
                </div>
            </div>
            
            <div class="quiz-actions">
                <button onclick="previousQuestion()" id="prevBtn" disabled>Previous</button>
                <button onclick="nextQuestion()" id="nextBtn" disabled>Next</button>
                <button onclick="submitQuiz()" id="submitBtn" style="display: none;">Submit Quiz</button>
            </div>
        </div>
        
        <script>
            let currentQuestion = 1;
            let totalQuestions = 3;
            let selectedAnswer = null;
            
            function selectOption(element, value) {
                // Clear previous selections
                document.querySelectorAll('.option').forEach(opt => {
                    opt.classList.remove('selected');
                    opt.querySelector('input').checked = false;
                });
                
                // Select current option
                element.classList.add('selected');
                element.querySelector('input').checked = true;
                selectedAnswer = value;
                
                // Enable next button
                document.getElementById('nextBtn').disabled = false;
                
                if (currentQuestion === totalQuestions) {
                    document.getElementById('submitBtn').style.display = 'inline-block';
                }
            }
            
            function nextQuestion() {
                if (currentQuestion < totalQuestions) {
                    currentQuestion++;
                    updateQuestion();
                    updateProgress();
                }
            }
            
            function previousQuestion() {
                if (currentQuestion > 1) {
                    currentQuestion--;
                    updateQuestion();
                    updateProgress();
                }
            }
            
            function updateQuestion() {
                const questions = [
                    {
                        text: "What is the primary purpose of formative assessment in education?",
                        options: [
                            "A) To assign final grades to students",
                            "B) To provide ongoing feedback for learning improvement",
                            "C) To rank students against each other",
                            "D) To fulfill administrative requirements"
                        ]
                    },
                    {
                        text: "Which learning theory emphasizes the importance of social interaction?",
                        options: [
                            "A) Behaviorism",
                            "B) Constructivism",
                            "C) Social Learning Theory",
                            "D) Cognitive Load Theory"
                        ]
                    },
                    {
                        text: "What is the most effective way to provide feedback to students?",
                        options: [
                            "A) Only point out mistakes",
                            "B) Give specific, actionable, and timely feedback",
                            "C) Provide feedback only at the end of the course",
                            "D) Use only numerical grades"
                        ]
                    }
                ];
                
                const question = questions[currentQuestion - 1];
                document.getElementById('questionText').textContent = question.text;
                
                const container = document.getElementById('optionsContainer');
                container.innerHTML = '';
                
                question.options.forEach((option, index) => {
                    const letter = String.fromCharCode(97 + index); // a, b, c, d
                    const label = document.createElement('label');
                    label.className = 'option';
                    label.onclick = () => selectOption(label, letter);
                    label.innerHTML = `<input type="radio" name="answer" value="${letter}" style="display: none;">${option}`;
                    container.appendChild(label);
                });
                
                // Reset selection
                selectedAnswer = null;
                document.getElementById('nextBtn').disabled = true;
                document.getElementById('prevBtn').disabled = currentQuestion === 1;
                document.getElementById('submitBtn').style.display = 'none';
            }
            
            function updateProgress() {
                const progress = (currentQuestion / totalQuestions) * 100;
                document.getElementById('progressBar').style.width = progress + '%';
            }
            
            function submitQuiz() {
                alert('Quiz submitted! In a real implementation, this would send results to the gradebook via LTI AGS.');
                notifyParent();
            }
            
            function notifyParent() {
                if (window.parent) {
                    window.parent.postMessage({
                        type: 'resize',
                        height: document.body.scrollHeight
                    }, '*');
                }
            }
            
            window.addEventListener('load', notifyParent);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@router.get("/content/default", summary="Default content iframe")
async def default_content(
    launch_id: Optional[str] = Query(None)
) -> HTMLResponse:
    """Serve default content in iframe."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>EduAnalytics Tools</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #fff;
                text-align: center;
            }
            .tools-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                max-width: 800px;
                margin: 20px auto;
            }
            .tool-card {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                transition: transform 0.2s;
                cursor: pointer;
            }
            .tool-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            .tool-icon {
                font-size: 2em;
                margin-bottom: 10px;
            }
            .tool-title {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            .tool-description {
                color: #666;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <h1>🎓 EduAnalytics Learning Tools</h1>
        <p>Enhance your learning experience with our comprehensive suite of educational tools.</p>
        
        <div class="tools-grid">
            <div class="tool-card" onclick="window.open('/api/lti/content/analytics', '_blank')">
                <div class="tool-icon">📊</div>
                <div class="tool-title">Analytics Dashboard</div>
                <div class="tool-description">
                    Real-time insights into student performance and engagement metrics.
                </div>
            </div>
            
            <div class="tool-card" onclick="window.open('/api/lti/content/ai-assistant', '_blank')">
                <div class="tool-icon">🤖</div>
                <div class="tool-title">AI Study Assistant</div>
                <div class="tool-description">
                    Get personalized help and study recommendations powered by AI.
                </div>
            </div>
            
            <div class="tool-card" onclick="window.open('/api/lti/content/quiz', '_blank')">
                <div class="tool-icon">📝</div>
                <div class="tool-title">Interactive Quizzes</div>
                <div class="tool-description">
                    Adaptive quizzes with instant feedback and detailed analytics.
                </div>
            </div>
            
            <div class="tool-card">
                <div class="tool-icon">📚</div>
                <div class="tool-title">Resource Library</div>
                <div class="tool-description">
                    Access curated educational resources and study materials.
                </div>
            </div>
            
            <div class="tool-card">
                <div class="tool-icon">👥</div>
                <div class="tool-title">Collaboration Hub</div>
                <div class="tool-description">
                    Connect with peers and participate in group activities.
                </div>
            </div>
            
            <div class="tool-card">
                <div class="tool-icon">🎯</div>
                <div class="tool-title">Goal Tracker</div>
                <div class="tool-description">
                    Set and track your learning goals and milestones.
                </div>
            </div>
        </div>
        
        <script>
            function notifyParent() {
                if (window.parent) {
                    window.parent.postMessage({
                        type: 'resize',
                        height: document.body.scrollHeight
                    }, '*');
                }
            }
            
            window.addEventListener('load', notifyParent);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@router.post("/cleanup", summary="Cleanup expired LTI data")
async def cleanup_lti_data() -> Dict[str, Any]:
    """Clean up expired LTI nonces and launches."""
    try:
        cleanup_counts = await lti_service.cleanup_expired_data()
        
        return {
            "success": True,
            "message": "LTI cleanup completed",
            "cleanup_counts": cleanup_counts,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LTI cleanup failed: {str(e)}"
        )


# LTI AGS (Assignment and Grade Services) endpoints

@router.post("/ags/line-items", summary="Create line item")
async def create_line_item(
    request: LineItemRequest,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Create a new line item on the LTI platform."""
    try:
        ags_service = get_lti_ags_service()
        
        line_item = LineItem(
            id="",  # Will be set by platform
            scoreMaximum=request.score_maximum,
            label=request.label,
            resourceId=request.resource_id,
            resourceLinkId=request.resource_link_id
        )
        
        created_line_item = await ags_service.create_line_item(
            request.platform_id,
            request.context_id,
            line_item
        )
        
        return {
            "success": True,
            "message": "Line item created successfully",
            "line_item": {
                "id": created_line_item.id,
                "label": created_line_item.label,
                "score_maximum": created_line_item.scoreMaximum,
                "resource_id": created_line_item.resourceId,
                "resource_link_id": created_line_item.resourceLinkId
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create line item: {str(e)}"
        )


@router.get("/ags/line-items", summary="Get line items")
async def get_line_items(
    platform_id: str = Query(..., description="LTI platform ID"),
    context_id: str = Query(..., description="Course context ID"),
    resource_link_id: Optional[str] = Query(None, description="Resource link ID"),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get line items from the LTI platform."""
    try:
        ags_service = get_lti_ags_service()
        
        line_items = await ags_service.get_line_items(
            platform_id,
            context_id,
            resource_link_id
        )
        
        return {
            "success": True,
            "line_items": [
                {
                    "id": item.id,
                    "label": item.label,
                    "score_maximum": item.scoreMaximum,
                    "resource_id": item.resourceId,
                    "resource_link_id": item.resourceLinkId,
                    "tag": item.tag,
                    "start_date_time": item.startDateTime,
                    "end_date_time": item.endDateTime
                }
                for item in line_items
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get line items: {str(e)}"
        )


@router.post("/ags/submit-grade", summary="Submit grade to platform")
async def submit_grade(
    request: GradeSubmissionRequest,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Submit a single grade to the LTI platform."""
    try:
        ags_service = get_lti_ags_service()
        
        success = await ags_service.sync_grade_to_platform(
            request.platform_id,
            request.context_id,
            request.assignment_id,
            request.student_id,
            request.score,
            request.max_score,
            request.comment
        )
        
        return {
            "success": success,
            "message": "Grade submitted successfully" if success else "Grade submission failed",
            "assignment_id": request.assignment_id,
            "student_id": request.student_id,
            "score": request.score,
            "max_score": request.max_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit grade: {str(e)}"
        )


@router.post("/ags/bulk-sync-grades", summary="Bulk sync grades")
async def bulk_sync_grades(
    request: BulkGradeSyncRequest,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Bulk sync all grades for an assignment to the LTI platform."""
    try:
        ags_service = get_lti_ags_service()
        
        result = await ags_service.bulk_sync_grades(
            request.platform_id,
            request.context_id,
            request.assignment_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk sync grades: {str(e)}"
        )


@router.get("/ags/sync-history", summary="Get grade sync history")
async def get_grade_sync_history(
    assignment_id: Optional[int] = Query(None, description="Assignment ID"),
    student_id: Optional[int] = Query(None, description="Student ID"),
    days: int = Query(7, description="Number of days to look back"),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Get grade synchronization history."""
    try:
        ags_service = get_lti_ags_service()
        
        history = await ags_service.get_sync_history(
            assignment_id=assignment_id,
            student_id=student_id,
            days=days
        )
        
        return {
            "success": True,
            "sync_history": history,
            "total_records": len(history),
            "filters": {
                "assignment_id": assignment_id,
                "student_id": student_id,
                "days": days
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync history: {str(e)}"
        )


@router.post("/ags/auto-sync/{assignment_id}", summary="Enable auto-sync for assignment")
async def enable_auto_sync(
    assignment_id: int,
    platform_id: str = Query(..., description="LTI platform ID"),
    context_id: str = Query(..., description="Course context ID"),
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Enable automatic grade synchronization for an assignment."""
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            # Update assignment to enable auto-sync
            update_query = """
            UPDATE assignments 
            SET lti_auto_sync = true,
                lti_platform_id = :platform_id,
                lti_context_id = :context_id,
                updated_at = NOW()
            WHERE id = :assignment_id
            """
            
            result = await db.execute(text(update_query), {
                "assignment_id": assignment_id,
                "platform_id": platform_id,
                "context_id": context_id
            })
            
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignment not found"
                )
            
            await db.commit()
            
            return {
                "success": True,
                "message": "Auto-sync enabled for assignment",
                "assignment_id": assignment_id,
                "platform_id": platform_id,
                "context_id": context_id
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable auto-sync: {str(e)}"
        )


@router.delete("/ags/auto-sync/{assignment_id}", summary="Disable auto-sync for assignment")
async def disable_auto_sync(
    assignment_id: int,
    current_user: User = Depends(require_role(UserRole.teacher, UserRole.admin))
) -> Dict[str, Any]:
    """Disable automatic grade synchronization for an assignment."""
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            # Update assignment to disable auto-sync
            update_query = """
            UPDATE assignments 
            SET lti_auto_sync = false,
                updated_at = NOW()
            WHERE id = :assignment_id
            """
            
            result = await db.execute(text(update_query), {
                "assignment_id": assignment_id
            })
            
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignment not found"
                )
            
            await db.commit()
            
            return {
                "success": True,
                "message": "Auto-sync disabled for assignment",
                "assignment_id": assignment_id
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable auto-sync: {str(e)}"
        )


@router.get("/ags/status", summary="Get AGS service status")
async def get_ags_status(
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Get LTI AGS service status and statistics."""
    try:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            # Get sync statistics
            stats_query = """
            SELECT 
                COUNT(*) as total_syncs,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_syncs,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_syncs,
                COUNT(DISTINCT assignment_id) as assignments_with_sync,
                COUNT(DISTINCT student_id) as students_synced
            FROM lti_grade_sync_log
            WHERE synced_at >= NOW() - INTERVAL '7 days'
            """
            
            result = await db.execute(text(stats_query))
            stats = dict(result.fetchone()._mapping) if result.rowcount > 0 else {}
            
            # Get recent sync activity
            recent_query = """
            SELECT 
                DATE_TRUNC('day', synced_at) as sync_date,
                COUNT(*) as sync_count,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count
            FROM lti_grade_sync_log
            WHERE synced_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE_TRUNC('day', synced_at)
            ORDER BY sync_date DESC
            """
            
            result = await db.execute(text(recent_query))
            recent_activity = [
                {
                    "date": row.sync_date.strftime("%Y-%m-%d"),
                    "total_syncs": row.sync_count,
                    "successful_syncs": row.success_count,
                    "success_rate": (row.success_count / row.sync_count * 100) if row.sync_count > 0 else 0
                }
                for row in result.fetchall()
            ]
            
            # Calculate success rate
            total_syncs = stats.get("total_syncs", 0)
            successful_syncs = stats.get("successful_syncs", 0)
            success_rate = (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0
            
            return {
                "success": True,
                "service_status": "active",
                "statistics": {
                    "total_syncs_7d": total_syncs,
                    "successful_syncs_7d": successful_syncs,
                    "failed_syncs_7d": stats.get("failed_syncs", 0),
                    "success_rate": round(success_rate, 2),
                    "assignments_with_sync": stats.get("assignments_with_sync", 0),
                    "students_synced": stats.get("students_synced", 0)
                },
                "recent_activity": recent_activity,
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AGS status: {str(e)}"
        )
