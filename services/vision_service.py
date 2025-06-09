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
        self.context_manager = None  # Will be set by VisionService
        
        try:
            self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
            print(f"✅ VisionManager initialized for: {self.provider_name} - {self.model_name}")
        except Exception as e:
            self.client = None
            self.is_healthy = False
            self.last_error = str(e)
            print(f"❌ CRITICAL: Failed to initialize VisionManager for {self.provider_name}: {e}")

    def set_context_manager(self, context_manager):
        """Set the shared context manager"""
        self.context_manager = context_manager

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
                    temperature=0.45,  # Lower temperature for more focused analysis
                    max_tokens=8100,
                    top_p=0.95
                ),
                timeout=75.0  # 60 second timeout for vision analysis
            )
            
            analysis = chat_completion.choices[0].message.content.strip()
            
            # Add vision analysis to conversation history if context manager available
            if self.context_manager:
                self.context_manager.add_ai_response(analysis, "vision")
            
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
            error_msg = f"Vision analysis timeout for {self.provider_name}. Request exceeded 45 seconds - try with fewer screenshots or simpler images."
            self.is_healthy = False
            self.last_error = "Request timeout (45s)"
            self.error_count += 1
            print(f"⏱️ TIMEOUT: {self.provider_name}-{self.model_name} vision analysis timed out after 45s")
            
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
        self.active_vision_providers: Dict[str, VisionManager] = {}
        self.context_manager = None

    def set_context_manager(self, context_manager):
        """Set the shared context manager for all vision managers"""
        self.context_manager = context_manager
        # Update all existing vision managers
        for manager in self.vision_managers.values():
            manager.set_context_manager(context_manager)
        
    def load_vision_providers(self, primary_config: Optional[Dict] = None, secondary_config: Optional[Dict] = None) -> bool:
        """Load active vision providers based on user selection."""
        self.active_vision_providers = {}
        
        if primary_config and primary_config.get('provider') and primary_config.get('model'):
            manager = self._create_vision_manager(primary_config['provider'], primary_config['model'])
            if manager:
                self.active_vision_providers['primary'] = manager

        if secondary_config and secondary_config.get('provider') and secondary_config.get('model'):
            manager = self._create_vision_manager(secondary_config['provider'], secondary_config['model'])
            if manager:
                self.active_vision_providers['secondary'] = manager
        
        print(f"✅ VisionService configured with {len(self.active_vision_providers)} active vision models.")
        return len(self.active_vision_providers) > 0

    def _create_vision_manager(self, provider_name: str, model_name: str) -> Optional[VisionManager]:
        """Create and return a vision manager for a given provider and model."""
        try:
            with open("ai_providers.json", "r") as f:
                providers_config = json.load(f)

            for provider_config in providers_config:
                if provider_config["name"] == provider_name:
                    manager = VisionManager(
                        provider_name=provider_name,
                        base_url=provider_config["baseURL"],
                        api_key=provider_config["apiKey"],
                        model_name=model_name
                    )
                    if self.context_manager:
                        manager.set_context_manager(self.context_manager)
                    return manager
            return None
        except Exception as e:
            print(f"❌ Failed to create vision manager for {provider_name}: {e}")
            return None
    
    def get_vision_manager(self, provider_name: str, model_name: str) -> Optional[VisionManager]:
        """Get a specific vision manager, checking active providers first."""
        # Check active providers first
        for key, manager in self.active_vision_providers.items():
            if manager.provider_name == provider_name and manager.model_name == model_name:
                return manager
        
        # Fallback to creating a new one if not found in active
        print(f"⚠️ Vision manager for {provider_name} - {model_name} not found in active providers. Creating on-the-fly.")
        return self._create_vision_manager(provider_name, model_name)
    
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
        
        # Determine primary programming language
        primary_language = "Java"  # Default fallback
        language_context = ""
        sql_available = False
        
        if languages and len(languages) > 0:
            # Filter out SQL to find primary programming language
            programming_languages = [lang for lang in languages if lang.lower() != 'sql']
            sql_available = 'sql' in [lang.lower() for lang in languages]
            
            if programming_languages:
                primary_language = programming_languages[0]
                other_languages = programming_languages[1:] if len(programming_languages) > 1 else []
                
                language_context = f"**Primary Language**: {primary_language}\n"
                if other_languages:
                    language_context += f"**Alternative Languages**: {', '.join(other_languages)}\n"
            else:
                # Only SQL was selected, still use Java for programming
                language_context = f"**Primary Language**: {primary_language} (default)\n"
        else:
            language_context = f"**Primary Language**: {primary_language} (default)\n"
        
        # Add conditional SQL support
        sql_instructions = ""
        if sql_available:
            sql_instructions = f"""
**🗄️ CONDITIONAL SQL ANALYSIS**: If and ONLY if the screenshots contain database-related content (tables, schemas, SQL queries, ER diagrams), provide additional SQL analysis:

### Database Context (Only if detected)
- Document any table structures found
- Note relationships and foreign keys  
- Provide SQL query solutions alongside the main programming solution

### SQL Solutions (Only if database content present) - give top 3 optimized solutions starting from most optimized.
```sql
-- SQL approach 1: [Brief description]
SELECT ... FROM ... WHERE ...;

-- SQL approach 2: [Alternative approach]  
SELECT ... FROM ... JOIN ... ON ...;
```

---
"""

        return f"""You are an expert coding interview assistant. Analyze the screenshots provided and give a comprehensive solution in {primary_language}.

{language_context}
{sql_instructions}

# 🎯 PROBLEM ANALYSIS

## Problem Understanding
Consolidate information from ALL screenshots:
- **Problem:** [Clear restatement]
- **Input/Output:** [Format and examples]
- **Constraints:** [Key limitations]
- **Core Challenge:** [Main algorithmic difficulty]

# 🚀 SOLUTION APPROACHES

## Approach 1: [OPTIMAL SOLUTION]
**Algorithm:** [Name/technique]
**Time:** O(?) | **Space:** O(?)

```{primary_language.lower()}
// Approach 1: [Brief description]
// Time: O(?), Space: O(?)

[Complete, production-ready code with comments]
```

**Walkthrough:** [Brief example execution]
**Why this works:** [Key insight]

---

## Approach 2: [ALTERNATIVE SOLUTION]
**Algorithm:** [Different technique]
**Time:** O(?) | **Space:** O(?)

```{primary_language.lower()}
// Approach 2: [Brief description]  
// Time: O(?), Space: O(?)

[Alternative implementation with comments]
```

**Walkthrough:** [Brief example execution]
**Trade-offs:** [When to use this vs Approach 1]

# 📊 COMPARISON & INTERVIEW STRATEGY

| Aspect | Approach 1 | Approach 2 |
|--------|------------|------------|
| **Time** | O(?) | O(?) |
| **Space** | O(?) | O(?) |
| **Complexity** | [Simple/Complex] | [Simple/Complex] |

**Interview Recommendation:** Present Approach 1 first, then discuss Approach 2 as optimization or alternative.

**Edge Cases:** [Key boundary conditions to mention]
**Follow-up Questions:** [Likely interviewer questions and responses]

{sql_instructions if sql_available else ""}

Be concise but thorough. Focus on interview-ready explanations and production-quality code in {primary_language}."""

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