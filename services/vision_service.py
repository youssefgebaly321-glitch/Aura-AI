import json
import asyncio
import base64
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from openai import AsyncOpenAI, APIStatusError
from core.config import settings

class VisionManager:
    """Vision AI Manager for screenshot analysis and code problem solving"""
    
    def __init__(self, provider_name: str, base_url: str, api_key: str, model_name: str):
        self.provider_name = provider_name
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key
        self.is_healthy = True
        self.last_error = None
        self.error_count = 0
        self.last_success_time = datetime.now()
        
        try:
            self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
            print(f"✅ VisionManager initialized for: {self.provider_name} - {self.model_name}")
        except Exception as e:
            self.client = None
            self.is_healthy = False
            self.last_error = str(e)
            print(f"❌ CRITICAL: Failed to initialize VisionManager for {self.provider_name}: {e}")

    async def health_check(self) -> bool:
        """Check if the vision provider is healthy and responsive"""
        if not self.client:
            return False
            
        try:
            # Quick test call to verify connectivity
            await asyncio.wait_for(self.client.models.list(), timeout=5.0)
            self.is_healthy = True
            self.error_count = 0
            self.last_success_time = datetime.now()
            return True
        except asyncio.TimeoutError:
            self.is_healthy = False
            self.last_error = "Connection timeout"
            self.error_count += 1
            return False
        except Exception as e:
            self.is_healthy = False
            self.last_error = str(e)
            self.error_count += 1
            return False

    async def analyze_screenshots(self, prompt: str, screenshots: List[str], languages: List[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Analyze screenshots with vision AI and provide comprehensive coding assistance"""
        if not self.client:
            return "I'm sorry, the vision AI service is not available at this time.", {
                "error": "No client available",
                "provider": self.provider_name,
                "model": self.model_name
            }
        
        try:
            # Prepare the message content with text and images
            content = [{"type": "text", "text": prompt}]
            
            # Add screenshots to the content
            for i, screenshot_data_url in enumerate(screenshots):
                # Ensure proper data URL format
                if not screenshot_data_url.startswith('data:image/'):
                    screenshot_data_url = f"data:image/jpeg;base64,{screenshot_data_url}"
                
                content.append({
                    "type": "image_url",
                    "image_url": {"url": screenshot_data_url}
                })
            
            print(f"🔍 Analyzing {len(screenshots)} screenshots with {self.provider_name}-{self.model_name}")
            
            # Make API call with timeout
            chat_completion = await asyncio.wait_for(
                self.client.chat.completions.create(
                    messages=[{
                        "role": "user", 
                        "content": content
                    }],
                    model=self.model_name,
                    temperature=0.4,  # Lower temperature for more focused analysis
                    max_tokens=8000,
                    top_p=0.9
                ),
                timeout=60.0  # 60 second timeout for vision analysis
            )
            
            analysis = chat_completion.choices[0].message.content.strip()
            
            # Update health status
            self.is_healthy = True
            self.error_count = 0
            self.last_success_time = datetime.now()
            
            return analysis, {
                "success": True,
                "provider": self.provider_name,
                "model": self.model_name,
                "screenshot_count": len(screenshots),
                "languages": languages or [],
                "response_time": datetime.now().isoformat(),
                "analysis_length": len(analysis)
            }
            
        except asyncio.TimeoutError:
            error_msg = f"Vision analysis timeout for {self.provider_name}. The request took too long to process."
            self.is_healthy = False
            self.last_error = "Request timeout"
            self.error_count += 1
            print(f"⏱️ TIMEOUT: {self.provider_name}-{self.model_name} vision analysis timed out")
            
            return error_msg, {
                "error": "timeout",
                "provider": self.provider_name,
                "model": self.model_name,
                "screenshot_count": len(screenshots)
            }
            
        except APIStatusError as e:
            error_msg = f"Vision API error from {self.provider_name}: {e.message}"
            self.is_healthy = False
            self.last_error = f"API Error: {e.status_code} - {e.message}"
            self.error_count += 1
            print(f"🚨 API ERROR: {self.provider_name}-{self.model_name}: {e.status_code} - {e.message}")
            
            return error_msg, {
                "error": "api_error",
                "status_code": e.status_code,
                "provider": self.provider_name,
                "model": self.model_name,
                "screenshot_count": len(screenshots)
            }
            
        except Exception as e:
            error_msg = f"Unexpected error during vision analysis with {self.provider_name}. Please try again."
            self.is_healthy = False
            self.last_error = str(e)
            self.error_count += 1
            print(f"❌ UNEXPECTED ERROR: {self.provider_name}-{self.model_name} vision analysis: {e}")
            
            return error_msg, {
                "error": "unexpected_error",
                "message": str(e),
                "provider": self.provider_name,
                "model": self.model_name,
                "screenshot_count": len(screenshots)
            }

    def get_status(self) -> Dict[str, Any]:
        """Get current status of this vision manager"""
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "is_healthy": self.is_healthy,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_success": self.last_success_time.isoformat() if self.last_success_time else None,
            "supports_vision": True
        }

class VisionService:
    """Service for managing vision analysis requests and providers"""
    
    def __init__(self):
        self.vision_managers: Dict[str, VisionManager] = {}
        
    def load_vision_providers(self) -> bool:
        """Load available vision providers from configuration"""
        try:
            with open("ai_providers.json", "r") as f:
                providers_config = json.load(f)
            
            vision_providers_loaded = 0
            
            for provider_config in providers_config:
                if provider_config.get("supportsVision") and provider_config.get("visionModels"):
                    provider_name = provider_config["name"]
                    
                    # Create vision managers for each vision model
                    for model_name in provider_config["visionModels"]:
                        manager_key = f"{provider_name}_{model_name}"
                        
                        self.vision_managers[manager_key] = VisionManager(
                            provider_name=provider_name,
                            base_url=provider_config["baseURL"],
                            api_key=provider_config["apiKey"],
                            model_name=model_name
                        )
                        vision_providers_loaded += 1
            
            print(f"✅ VisionService initialized with {vision_providers_loaded} vision models")
            return vision_providers_loaded > 0
            
        except Exception as e:
            print(f"❌ CRITICAL: Failed to load vision providers: {e}")
            return False
    
    def get_vision_manager(self, provider_name: str, model_name: str) -> Optional[VisionManager]:
        """Get a specific vision manager"""
        manager_key = f"{provider_name}_{model_name}"
        return self.vision_managers.get(manager_key)
    
    async def analyze_coding_problem(self, provider_name: str, model_name: str, 
                                   screenshots: List[str], languages: List[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Analyze coding problem screenshots with comprehensive prompting"""
        
        vision_manager = self.get_vision_manager(provider_name, model_name)
        if not vision_manager:
            return f"Vision model {provider_name} - {model_name} not available.", {
                "error": "vision_model_not_found",
                "provider": provider_name,
                "model": model_name
            }
        
        # Generate comprehensive coding prompt
        prompt = self.generate_coding_analysis_prompt(languages)
        
        # Perform vision analysis
        return await vision_manager.analyze_screenshots(prompt, screenshots, languages)
    
    def generate_coding_analysis_prompt(self, languages: List[str] = None) -> str:
        """Generate a comprehensive prompt for coding problem analysis"""
        
        language_context = ""
        if languages and len(languages) > 0:
            primary_language = languages[0]
            other_languages = languages[1:] if len(languages) > 1 else []
            
            language_context = f"**Primary Language**: {primary_language}\n"
            if other_languages:
                language_context += f"**Alternative Languages**: {', '.join(other_languages)}\n"
        else:
            language_context = "**Languages**: Use Python as primary, but mention alternatives\n"
        
        return f"""You are an expert coding interview assistant and competitive programming mentor. Analyze the provided screenshot(s) of coding problems and provide comprehensive, interview-ready assistance.

{language_context}

## Analysis Framework

Please provide a **structured, comprehensive analysis** following this format:

### 1. 🎯 **Problem Understanding**
- **Problem Statement**: Clearly restate what the problem is asking
- **Input/Output Format**: Describe expected inputs and outputs
- **Constraints**: List all constraints and their implications
- **Edge Cases**: Identify potential edge cases to consider

### 2. 🧠 **Approach & Algorithm**
- **Intuition**: Explain the key insight to solve this problem
- **Algorithm Choice**: Why this approach is optimal
- **Time Complexity**: Big O analysis with explanation
- **Space Complexity**: Memory usage analysis
- **Alternative Approaches**: Brief mention of other possible solutions

### 3. 💻 **Implementation**
```python
# Provide clean, well-commented code solution
# Use descriptive variable names
# Include helpful comments explaining key steps
```

### 4. 🔍 **Step-by-Step Walkthrough**
- Walk through the solution with a concrete example
- Explain each major step and why it works
- Show how the algorithm progresses through the data

### 5. 🧪 **Testing & Validation**
- **Test Cases**: Show how solution works with given examples
- **Edge Case Testing**: Demonstrate handling of edge cases
- **Debugging Tips**: Common mistakes to avoid

### 6. 🎤 **Interview Communication**
- **How to Present**: How to explain this solution clearly in an interview
- **Key Points to Emphasize**: Most important aspects to highlight
- **Follow-up Questions**: What an interviewer might ask next
- **Optimization Discussion**: How you might improve the solution

### 7. 🔄 **Alternative Solutions**
- **Different Approaches**: Other ways to solve this problem
- **Trade-offs**: When to use which approach
- **Complexity Comparisons**: How different solutions compare

### 8. 💡 **Related Concepts**
- **Data Structures Used**: Why these data structures are chosen
- **Algorithmic Patterns**: What patterns this problem demonstrates
- **Similar Problems**: Related problems that use similar techniques

## Guidelines:
- **Be Educational**: Focus on understanding, not just the answer
- **Be Interview-Ready**: Format responses for interview scenarios
- **Be Comprehensive**: Cover all aspects a good interview answer should include
- **Be Practical**: Include real implementation details and gotchas
- **Be Clear**: Use simple language and clear explanations

## Code Quality Standards:
- Clean, readable code with proper indentation
- Meaningful variable and function names
- Helpful comments for complex logic
- Error handling where appropriate
- Follow language best practices

Analyze the screenshot(s) and provide this comprehensive assistance to help succeed in the coding interview!"""

    async def get_all_vision_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all vision providers"""
        status = {}
        
        for manager_key, manager in self.vision_managers.items():
            try:
                # Perform health check
                is_healthy = await manager.health_check()
                status[manager_key] = manager.get_status()
                status[manager_key]["health_check_result"] = is_healthy
            except Exception as e:
                status[manager_key] = {
                    "provider": manager.provider_name,
                    "model": manager.model_name,
                    "is_healthy": False,
                    "error": str(e),
                    "health_check_result": False
                }
        
        return status

# Global vision service instance
vision_service = VisionService()

# Verification function
async def verify_vision_provider_connection(base_url: str, api_key: str, model_name: str) -> bool:
    """Verify a vision provider connection"""
    try:
        temp_client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        await asyncio.wait_for(temp_client.models.list(), timeout=10.0)
        print(f"✅ Vision connection to {base_url} with model {model_name} is valid.")
        return True
    except asyncio.TimeoutError:
        print(f"⏱️ TIMEOUT: Vision connection to {base_url} timed out")
        return False
    except APIStatusError as e:
        print(f"❌ ERROR: Vision API key verification failed for {base_url}. Status: {e.status_code}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Vision provider verification error for {base_url}: {e}")
        return False 