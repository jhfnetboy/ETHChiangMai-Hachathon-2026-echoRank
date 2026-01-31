import { GoogleGenerativeAI } from '@google/generative-ai';
import dotenv from 'dotenv';

dotenv.config();

// Initialize Gemini
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');

export interface ScrapingRule {
    domain: string;
    event_card_selector: string;
    title_selector: string;
    date_selector: string;
    location_selector: string;
    link_selector: string;
}

export async function generateSelectorsWithAI(domain: string, htmlSnippet: string): Promise<ScrapingRule> {
    console.log(`🤖 Asking Gemini to generate selectors for ${domain}...`);

    try {
        const model = genAI.getGenerativeModel({ model: "gemini-pro" });

        const prompt = `
        You are an expert web scraper. I need CSS selectors to extract event information from the following HTML code snippet from ${domain}.
        
        HTML Snippet:
        \`\`\`html
        ${htmlSnippet}
        \`\`\`
        
        Please return a JSON object with the following keys:
        - event_card_selector: The selector for the container element of each individual event.
        - title_selector: The selector for the event title (relative to the card).
        - date_selector: The selector for the event date/time (relative to the card).
        - location_selector: The selector for the event location (relative to the card).
        - link_selector: The selector for the main link to the event details (relative to the card).
        
        If a specific field is not found, use "null".
        Return ONLY the raw JSON string, no markdown code blocks.
        `;

        const result = await model.generateContent(prompt);
        const response = await result.response;
        const text = response.text();
        
        // Clean up markdown code blocks if present (Gemini sometimes adds them despite instructions)
        const jsonStr = text.replace(/```json/g, '').replace(/```/g, '').trim();
        
        const selectors = JSON.parse(jsonStr);
        
        return {
            domain,
            event_card_selector: selectors.event_card_selector || 'body',
            title_selector: selectors.title_selector || 'h1',
            date_selector: selectors.date_selector || 'time',
            location_selector: selectors.location_selector || 'div',
            link_selector: selectors.link_selector || 'a'
        };

    } catch (error) {
        console.error("❌ AI Generation Failed:", error);
        // Fallback default
        return {
            domain,
            event_card_selector: 'div.event-card', 
            title_selector: 'h3',
            date_selector: '.date',
            location_selector: '.location',
            link_selector: 'a'
        };
    }
}
