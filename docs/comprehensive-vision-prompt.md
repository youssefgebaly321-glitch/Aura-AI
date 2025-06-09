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

