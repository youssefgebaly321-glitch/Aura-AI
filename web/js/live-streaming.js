// Live Interview Streaming Module
// Handles text streaming, animations, and content parsing with markdown support

import { MarkdownProcessor } from './markdown-processor.js';

export class LiveStreaming {
    constructor(config = {}) {
        this.config = {
            enableStreaming: true,
            streamingSpeed: 15, // milliseconds between words (lower = faster)
            aiStreamingSpeed: 5, // 2x faster than before
            enableMarkdown: true, // Enable markdown processing
            markdownSpeed: 20, // Faster speed for markdown elements (headers, lists)
            ...config
        };
        
        // Initialize markdown processor
        this.markdownProcessor = new MarkdownProcessor({
            preserveCodeBlocks: true,
            enableNestedLists: true,
            professionalStyling: true
        });
    }

    // Update configuration
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
    }

    // Stream content with typing effect and markdown support
    async streamContent(container, content, speed = null) {
        const actualSpeed = speed || this.config.streamingSpeed;
        
        if (!this.config.enableStreaming) {
            // If streaming is disabled, show content immediately
            if (this.config.enableMarkdown) {
                this.displayInstantMarkdown(container, content);
            } else {
                this.displayInstantText(container, content);
            }
            container.parentElement.classList.add('complete');
            return;
        }

        // Process with markdown if enabled
        if (this.config.enableMarkdown) {
            await this.streamMarkdownContent(container, content, actualSpeed);
        } else {
            // Fallback to original logic
            if (content.includes('```')) {
                await this.streamComplexContent(container, content, actualSpeed);
            } else {
                await this.streamSimpleText(container, content, actualSpeed);
            }
        }
        
        container.parentElement.classList.add('complete');
    }

    // Stream simple text
    async streamSimpleText(container, text, speed, onProgress = null) {
        const words = text.split(' ');
        
        for (let i = 0; i < words.length; i++) {
            const wordSpan = document.createElement('span');
            wordSpan.className = 'word';
            wordSpan.textContent = words[i] + (i < words.length - 1 ? ' ' : '');
            
            container.appendChild(wordSpan);
            
            setTimeout(() => {
                wordSpan.style.opacity = '1';
            }, 10);
            
            await this.delay(speed);
            
            // Callback for scroll updates
            if (onProgress && i % 3 === 0) {
                onProgress();
            }
        }
        
        // Final callback
        if (onProgress) {
            onProgress();
        }
    }

    // Stream complex content with code
    async streamComplexContent(container, content, speed, onProgress = null) {
        const parts = this.parseContent(content);
        
        for (const part of parts) {
            if (part.type === 'text') {
                await this.streamSimpleText(container, part.content, speed, onProgress);
            } else if (part.type === 'code') {
                this.addCodeBlock(container, part.content, part.language);
                await this.delay(200); // Reduced delay for faster display
            }
            if (onProgress) onProgress();
        }
    }

    // Parse content for code blocks
    parseContent(content) {
        const parts = [];
        const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
        let lastIndex = 0;
        let match;

        while ((match = codeBlockRegex.exec(content)) !== null) {
            // Add text before code block
            if (match.index > lastIndex) {
                const textPart = content.substring(lastIndex, match.index);
                if (textPart.trim()) {
                    parts.push({ type: 'text', content: textPart.trim() });
                }
            }
            
            // Add code block
            parts.push({
                type: 'code',
                language: match[1] || 'javascript',
                content: match[2].trim()
            });
            
            lastIndex = match.index + match[0].length;
        }
        
        // Add remaining text
        if (lastIndex < content.length) {
            const remainingText = content.substring(lastIndex);
            if (remainingText.trim()) {
                parts.push({ type: 'text', content: remainingText.trim() });
            }
        }
        
        // If no code blocks found, return as simple text
        if (parts.length === 0) {
            parts.push({ type: 'text', content: content });
        }
        
        return parts;
    }

    // Add code block
    addCodeBlock(container, code, language) {
        const codeBlockDiv = document.createElement('div');
        codeBlockDiv.className = 'code-block';
        
        const headerDiv = document.createElement('div');
        headerDiv.className = 'code-header';
        
        // Create language tag
        const languageTag = document.createElement('span');
        languageTag.className = 'language-tag';
        languageTag.textContent = language;
        
        // Create copy button with proper event handling
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-btn';
        copyButton.innerHTML = '&#128203;'; // Clipboard icon
        copyButton.title = 'Copy code';
        copyButton.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(code);
                copyButton.textContent = '✅';
                copyButton.title = 'Copied!';
                setTimeout(() => {
                    copyButton.innerHTML = '&#128203;';
                    copyButton.title = 'Copy code';
                }, 2000);
            } catch (err) {
                console.error('Failed to copy code:', err);
                copyButton.textContent = '❌';
                copyButton.title = 'Failed to copy';
                setTimeout(() => {
                    copyButton.innerHTML = '&#128203;';
                    copyButton.title = 'Copy code';
                }, 2000);
            }
        });
        
        headerDiv.appendChild(languageTag);
        headerDiv.appendChild(copyButton);
        
        const preElement = document.createElement('pre');
        const codeElement = document.createElement('code');
        codeElement.className = `language-${language}`;
        codeElement.textContent = code;
        
        preElement.appendChild(codeElement);
        codeBlockDiv.appendChild(headerDiv);
        codeBlockDiv.appendChild(preElement);
        
        container.appendChild(codeBlockDiv);
        
        // Apply syntax highlighting
        if (window.Prism) {
            window.Prism.highlightElement(codeElement);
        }
    }

    // NEW: Stream markdown content with proper formatting
    async streamMarkdownContent(container, content, speed, onProgress = null) {
        try {
            // Parse content into structured blocks
            const blocks = this.markdownProcessor.parseContent(content);
            
            for (let i = 0; i < blocks.length; i++) {
                const block = blocks[i];
                
                if (block.type === 'code') {
                    // Use existing code block system
                    this.addCodeBlock(container, block.content, block.language);
                    await this.delay(50); // Much faster for code blocks
                } else if (block.type === 'header') {
                    await this.streamHeaderBlock(container, block);
                } else if (block.type === 'list') {
                    await this.streamListBlock(container, block, speed);
                } else if (block.type === 'paragraph') {
                    await this.streamParagraphBlock(container, block, speed);
                }
                
                // Progress callback
                if (onProgress) onProgress();
                
                // Reduced delay between blocks for better flow
                if (i < blocks.length - 1) {
                    await this.delay(40);
                }
            }
        } catch (error) {
            console.error('Markdown processing error:', error);
            // Fallback to simple text streaming
            await this.streamSimpleText(container, content, speed, onProgress);
        }
    }

    // Stream a header block
    async streamHeaderBlock(container, block) {
        const headerElement = document.createElement(`h${block.level}`);
        headerElement.className = `markdown-header markdown-h${block.level}`;
        headerElement.id = block.id;
        
        // Add empty header immediately so it's visible
        container.appendChild(headerElement);
        
        // Small delay to let CSS animation start, then stream content
        await this.delay(20);
        await this.streamTextIntoElement(headerElement, block.content, this.config.aiStreamingSpeed);
    }

    // Stream a list block
    async streamListBlock(container, block, speed) {
        const listTag = block.listType === 'numbered' ? 'ol' : 'ul';
        const listElement = document.createElement(listTag);
        listElement.className = `markdown-list markdown-${block.listType}-list`;
        
        // Add empty list immediately so it's visible
        container.appendChild(listElement);
        
        // Create all list items first, then stream content into them
        const listItems = [];
        for (let i = 0; i < block.items.length; i++) {
            const item = block.items[i];
            const listItem = document.createElement('li');
            
            let className = 'markdown-list-item';
            if (item.indent > 0) {
                className += ` indent-${Math.min(item.indent, 4)}`;
            }
            listItem.className = className;
            
            listElement.appendChild(listItem);
            listItems.push({ element: listItem, content: item.content });
        }
        
        // Small delay to let CSS animation start
        await this.delay(20);
        
        // Now stream content into each list item
        for (let i = 0; i < listItems.length; i++) {
            await this.streamTextIntoElement(listItems[i].element, listItems[i].content, speed);
            
            // Smaller delay between items for better flow
            if (i < listItems.length - 1) {
                await this.delay(20);
            }
        }
    }

    // Stream a paragraph block
    async streamParagraphBlock(container, block, speed) {
        if (!block.content || !block.content.trim()) {
            return; // Skip empty paragraphs
        }
        
        const paragraphElement = document.createElement('p');
        paragraphElement.className = 'markdown-paragraph';
        paragraphElement.id = block.id;
        
        // Add empty paragraph immediately so it's visible
        container.appendChild(paragraphElement);
        
        // Small delay to let CSS animation start, then stream content
        await this.delay(20);
        await this.streamTextIntoElement(paragraphElement, block.content, speed);
    }

    // Stream text into a specific element with HTML support
    async streamTextIntoElement(element, htmlContent, speed) {
        // Parse HTML content and stream it properly
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = htmlContent;
        
        // If there are HTML elements, we need to handle them specially
        if (tempDiv.children.length > 0) {
            // Process mixed HTML and text content
            await this.streamMixedContent(element, tempDiv, speed);
        } else {
            // Simple text content - stream word by word
            const text = tempDiv.textContent || htmlContent;
            await this.streamSimpleTextIntoElement(element, text, speed);
        }
    }

    // Stream mixed HTML and text content
    async streamMixedContent(targetElement, sourceElement, speed) {
        for (const child of sourceElement.childNodes) {
            if (child.nodeType === Node.TEXT_NODE) {
                const text = child.textContent.trim();
                if (text) {
                    await this.streamSimpleTextIntoElement(targetElement, text, speed);
                }
            } else if (child.nodeType === Node.ELEMENT_NODE) {
                // For inline formatted elements like <strong>, <em>, <code>
                const formattedElement = child.cloneNode(false); // Clone without children
                targetElement.appendChild(formattedElement);
                
                // Stream the content inside the formatted element
                if (child.textContent) {
                    await this.streamSimpleTextIntoElement(formattedElement, child.textContent, speed);
                }
                
                await this.delay(30); // Brief pause after formatted elements
            }
        }
    }

    // Stream simple text into an element
    async streamSimpleTextIntoElement(element, text, speed) {
        const words = text.split(' ');
        
        for (let i = 0; i < words.length; i++) {
            const word = words[i];
            if (word.trim()) {
                const wordSpan = document.createElement('span');
                wordSpan.className = 'word';
                wordSpan.textContent = word + (i < words.length - 1 ? ' ' : '');
                element.appendChild(wordSpan);
                
                setTimeout(() => {
                    wordSpan.style.opacity = '1';
                }, 10);
                
                await this.delay(speed);
            }
        }
    }

    // Display markdown content instantly (for interim updates)
    displayInstantMarkdown(container, content) {
        try {
            const blocks = this.markdownProcessor.parseContent(content);
            
            blocks.forEach(block => {
                if (block.type === 'code') {
                    this.addCodeBlock(container, block.content, block.language);
                } else {
                    const html = this.markdownProcessor.generateHTML(block);
                    if (html) {
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = html;
                        
                        // Move all children from temp div to container
                        while (tempDiv.firstChild) {
                            const element = tempDiv.firstChild;
                            container.appendChild(element);
                            
                            // Apply instant word styling to text content
                            this.applyInstantWordStyling(element);
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Instant markdown display error:', error);
            // Fallback to simple text
            this.displayInstantText(container, content);
        }
    }

    // Apply instant word styling to an element and its children
    applyInstantWordStyling(element) {
        if (element.nodeType === Node.TEXT_NODE) {
            // Don't process text nodes directly
            return;
        }
        
        if (element.nodeType === Node.ELEMENT_NODE) {
            // Check if this element has direct text content
            const walker = document.createTreeWalker(
                element,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            const textNodes = [];
            let node;
            while (node = walker.nextNode()) {
                if (node.textContent.trim()) {
                    textNodes.push(node);
                }
            }
            
            // Replace text nodes with word spans
            textNodes.forEach(textNode => {
                const text = textNode.textContent;
                const parent = textNode.parentNode;
                
                // Create word spans
                const words = text.split(' ');
                const fragment = document.createDocumentFragment();
                
                words.forEach((word, i) => {
                    if (word.trim()) {
                        const wordSpan = document.createElement('span');
                        wordSpan.className = 'word';
                        wordSpan.style.opacity = '1';
                        wordSpan.textContent = word + (i < words.length - 1 ? ' ' : '');
                        fragment.appendChild(wordSpan);
                    }
                });
                
                parent.replaceChild(fragment, textNode);
            });
        }
    }

    // Display text instantly (for interim updates)
    displayInstantText(container, text) {
        const words = text.split(' ');
        
        for (let i = 0; i < words.length; i++) {
            const wordSpan = document.createElement('span');
            wordSpan.className = 'word';
            wordSpan.style.opacity = '1'; // Show immediately
            wordSpan.textContent = words[i] + (i < words.length - 1 ? ' ' : '');
            container.appendChild(wordSpan);
        }
    }

    // Delay utility
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Configuration methods
    setStreamingEnabled(enabled) {
        this.config.enableStreaming = enabled;
    }

    setStreamingSpeed(speed) {
        this.config.streamingSpeed = Math.max(10, Math.min(100, speed)); // 10-100ms range
    }

    setAIStreamingSpeed(speed) {
        this.config.aiStreamingSpeed = Math.max(5, Math.min(50, speed)); // 5-50ms range
    }

    setMarkdownEnabled(enabled) {
        this.config.enableMarkdown = enabled;
    }

    setMarkdownSpeed(speed) {
        this.config.markdownSpeed = Math.max(50, Math.min(500, speed)); // 50-500ms range
    }

    getConfig() {
        return { ...this.config };
    }

    // Get markdown processor instance
    getMarkdownProcessor() {
        return this.markdownProcessor;
    }
} 