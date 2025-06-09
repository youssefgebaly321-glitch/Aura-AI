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
                    temperature=0.4,  # Lower temperature for more focused analysis
                    max_tokens=10000,
                    top_p=0.9
                ),
                timeout=60.0  # 60 second timeout for vision analysis
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

        return f"""You are an expert coding interview assistant and competitive programming mentor. I'm providing you with multiple screenshots that may contain:
- A coding problem statement
- Input/output examples  
- Constraints and requirements
- Database schemas, tables, or SQL queries (analyze only if present)
- Additional context or hints

**IMPORTANT**: Analyze ALL screenshots together as ONE COMPLETE problem. If multiple screenshots show the same problem from different angles, consolidate the information.

{language_context}
{sql_instructions}

## 📋 STRUCTURED ANALYSIS FORMAT

Please provide a **comprehensive analysis** with **clear separation** between problem understanding and each approach:

---

# 🎯 PROBLEM UNDERSTANDING & ANALYSIS

## 📖 Complete Problem Statement
Consolidate ALL information from ALL screenshots into one clear problem description:
- **What the problem is asking:** Clear restatement in simple terms
- **Input format:** Exact specifications from all sources
- **Output format:** Expected result structure
- **All constraints:** Every limitation mentioned across screenshots
- **Examples provided:** All input/output examples from screenshots

## 🔍 Key Insights & Edge Cases
- **Core challenge:** The main algorithmic/technical difficulty
- **Edge cases to consider:** Boundary conditions and special scenarios
- **Potential gotchas:** Common mistakes or tricky aspects
- **Problem category:** What type of algorithm/data structure problem this is

---
## Give best 2 approaches to solve the problem and it should be commonly used in interviews.

# 🚀 APPROACH 1: [NAME THE FIRST APPROACH]

## 💡 Strategy Overview
- **Algorithm choice:** What algorithm/technique we're using
- **Key insight:** Why this approach works
- **High-level plan:** Step-by-step strategy

## ⚙️ Technical Details
- **Time Complexity:** O(?) with detailed explanation
- **Space Complexity:** O(?) with memory breakdown
- **Data structures used:** What and why
- **Trade-offs:** Advantages of this approach

## 💻 Complete Implementation

```{primary_language.lower()}
// APPROACH 1: [Brief description]
// Time: O(?), Space: O(?)

[Provide complete, production-ready code]
// Include detailed comments explaining each step
// Use meaningful variable names
// Handle all edge cases properly
// Make it interview-ready
```

## 🔍 Step-by-Step Walkthrough
Walk through the algorithm with a concrete example:
1. **Initial state:** Starting condition
2. **Step-by-step execution:** How the algorithm progresses
3. **Key decisions:** Why we make certain choices at each step
4. **Final result:** How we arrive at the answer

## 🧪 Testing & Validation
- **Example execution:** Run through provided test cases
- **Edge case handling:** How the code handles boundary conditions
- **Correctness proof:** Why this algorithm works

---

# ⚡ APPROACH 2: [NAME THE SECOND APPROACH]

## 💡 Strategy Overview
- **Different algorithm:** Alternative technique/strategy
- **Key insight:** Different way of thinking about the problem
- **High-level plan:** Alternative step-by-step approach

## ⚙️ Technical Details
- **Time Complexity:** O(?) - compare with Approach 1
- **Space Complexity:** O(?) - memory trade-offs vs Approach 1
- **Data structures used:** Different choices and rationale
- **Trade-offs:** When this approach is better than Approach 1

## 💻 Complete Implementation

```{primary_language.lower()}
// APPROACH 2: [Brief description]
// Time: O(?), Space: O(?)

[Provide complete, alternative implementation]
// Show different algorithmic thinking
// Include comprehensive comments
// Demonstrate alternative problem-solving approach
// Handle edge cases with different strategy
```

## 🔍 Step-by-Step Walkthrough
Walk through this alternative approach:
1. **Different starting point:** How this approach begins differently
2. **Alternative execution:** Different algorithmic flow
3. **Key differences:** What makes this approach unique
4. **Final result:** Different path to the same answer

## 🧪 Testing & Validation
- **Example execution:** Same test cases, different algorithm
- **Edge case handling:** Alternative strategies for boundary conditions
- **Performance comparison:** When this outperforms Approach 1

---

# ⚖️ APPROACH COMPARISON & SELECTION

## 📊 Head-to-Head Analysis
| Aspect | Approach 1 | Approach 2 |
|--------|------------|------------|
| **Time Complexity** | O(?) | O(?) |
| **Space Complexity** | O(?) | O(?) |
| **Code Simplicity** | [Rating] | [Rating] |
| **Interview Friendliness** | [Assessment] | [Assessment] |

## 🎯 When to Choose Each Approach
- **Choose Approach 1 when:** Specific scenarios where it excels
- **Choose Approach 2 when:** Different scenarios where it's better
- **Interview recommendation:** Which to present first and why

## 🎤 Interview Strategy
- **Presentation order:** How to discuss both approaches
- **Time management:** Which to implement if time is limited
- **Follow-up handling:** Expected interviewer questions
- **Optimization discussion:** How to improve either solution

---

# 🔧 ADDITIONAL INSIGHTS

## 🌟 Alternative Approaches (Brief)
- **Approach 3:** Brief mention of other possible techniques
- **Advanced optimizations:** Potential improvements for either approach
- **Related patterns:** What other problems this prepares you for

## 💡 Key Takeaways
- **Core algorithmic insights:** Main concepts to remember
- **Problem-solving patterns:** Transferable techniques
- **Interview tips:** Specific advice for this problem type

{sql_instructions if sql_available else ""}

## 🎯 Analysis Guidelines:
- **Clear Separation**: Each approach gets its own complete section
- **Comprehensive Coverage**: Include everything from ALL screenshots
- **Interview-Ready**: Format for real interview presentation
- **Two Complete Solutions**: Fully implemented, testable code in {primary_language}
- **Strategic Thinking**: Help understand WHY each approach works
- **Professional Quality**: Clean, documented, production-ready code

Analyze ALL screenshots comprehensively and provide this **clearly separated** analysis focused on {primary_language} programming solutions!"""

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