"""CurioCut Infinite Claude Skills & MCP Tools Vault.
Provides a deep, high-converting catalog of underground Claude skills,
Model Context Protocol (MCP) servers, and open-source automation superpowers.

Used when:
1. Breaking tech news is slow/quiet.
2. The user wants dedicated Claude superpowers content.
3. Repost/Remake rotation needs fresh high-engagement utility tools.
"""
import random
import re

CLAUDE_SKILLS_CATALOG = [
    {
        "title": "The Claude Skill That Takes Over Your Browser",
        "tool_name": "Browser-Use Skill",
        "skill_category": "Web Automation",
        "cta_keyword": "BROWSE",
        "resource_url": "https://github.com/browser-use/browser-use",
        "premise": "There is a secret Claude skill called Browser-Use that physically opens Google Chrome, searches Google, clicks buttons, and books flights or applies to jobs completely on autopilot. A developer used it to scrape real estate listings across forty sites in ten minutes for zero dollars.",
        "steps": [
            "Install the browser-use python package",
            "Give Claude the instruction like 'Find the cheapest flight to Tokyo'",
            "Watch Chrome open and physically book and research by itself"
        ]
    },
    {
        "title": "Turn Any Figma Design Into React Code With Claude",
        "tool_name": "Figma-to-Code Skill",
        "skill_category": "Frontend Development",
        "cta_keyword": "FIGMA",
        "resource_url": "https://github.com/GLIPS-TEAM/figma-to-react",
        "premise": "Instead of spending forty hours translating Figma mockups into code, this Claude skill reads your Figma file directly and outputs responsive React, Tailwind, and TypeScript components with clean animations in four seconds.",
        "steps": [
            "Connect your Figma API token to Claude",
            "Paste the link to your Figma frame or button component",
            "Copy the production-ready React and Tailwind code straight into your app"
        ]
    },
    {
        "title": "The Secret Skill That Connects Claude to Any Database",
        "tool_name": "Postgres-MCP Server",
        "skill_category": "Data & Backend",
        "cta_keyword": "DATA",
        "resource_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/postgres",
        "premise": "Data analysts are replacing expensive Business Intelligence tools with the official Postgres MCP skill. You ask Claude 'Who are our top ten customers this month?' and it writes the SQL, queries your database safely, and charts the revenue numbers instantly.",
        "steps": [
            "Add the Postgres MCP server to your Claude configuration",
            "Connect your local database URL with read-only access",
            "Ask any question about your data in plain English"
        ]
    },
    {
        "title": "Claude Autonomous Bug Fixer That Submits Pull Requests",
        "tool_name": "GitHub-PR Skill",
        "skill_category": "Software Engineering",
        "cta_keyword": "GITHUB",
        "resource_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/github",
        "premise": "Developers connected the GitHub MCP skill to Claude Code. When someone opens a bug issue on GitHub, Claude reads the stack trace, finds the exact broken function in the repository, writes the unit test, and submits a verified pull request while you sleep.",
        "steps": [
            "Add the GitHub MCP server to Claude Code",
            "Point Claude to your open GitHub issues",
            "Watch it clone, branch, refactor, and open pull requests automatically"
        ]
    },
    {
        "title": "Give Claude Permanent Long-Term Memory Across All Projects",
        "tool_name": "Memory-MCP Server",
        "skill_category": "Productivity",
        "cta_keyword": "MEMORY",
        "resource_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/memory",
        "premise": "The most annoying part of AI is having to re-explain your company, your coding style, and your preferences every single chat. The Memory MCP skill creates a local knowledge graph that lets Claude remember everything you teach it forever.",
        "steps": [
            "Enable the Memory MCP skill in your Claude settings",
            "Tell Claude your preferred tech stack and coding conventions once",
            "Every future session automatically remembers your exact preferences"
        ]
    },
    {
        "title": "The Claude Skill That Summarizes 500 Unread Slack Messages",
        "tool_name": "Slack-Triage Skill",
        "skill_category": "Workplace Automation",
        "cta_keyword": "SLACK",
        "resource_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/slack",
        "premise": "Instead of wasting forty-five minutes every morning reading endless Slack threads, this Claude skill scans all your unread channels, filters out watercooler chatter, and gives you a three-bullet briefing of only decisions that need your approval.",
        "steps": [
            "Connect the Slack MCP integration to Claude",
            "Ask Claude to summarize unread notifications since yesterday",
            "Review your executive summary in thirty seconds"
        ]
    },
    {
        "title": "Extract Messy PDF Tables Into Clean CSVs in 2 Seconds",
        "tool_name": "PDF-Whisperer Skill",
        "skill_category": "Finance & Data",
        "cta_keyword": "PDF",
        "resource_url": "https://github.com/modelcontextprotocol/servers",
        "premise": "Accounting firms charge thousands of dollars to manually retype scanned PDF invoices and bank statements into Excel. This Claude skill parses multi-column PDFs, fixes broken rows, and outputs clean CSV spreadsheets ready for bookkeeping.",
        "steps": [
            "Drop your PDF or scanned bank statement into the Claude window",
            "Say 'Extract all transactions into clean CSV format'",
            "Download your spreadsheet with zero manual data entry"
        ]
    },
    {
        "title": "Audit Any Website for Speed and SEO in 5 Seconds",
        "tool_name": "Puppeteer-Lighthouse Skill",
        "skill_category": "Marketing & SEO",
        "cta_keyword": "AUDIT",
        "resource_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/puppeteer",
        "premise": "Agencies charge five hundred dollars for website SEO and performance audits. With the Puppeteer MCP skill, Claude opens any live website in headless Chrome, runs Lighthouse diagnostic metrics, and writes the exact CSS and image fixes to make it load instantly.",
        "steps": [
            "Give Claude the URL of any website you want to analyze",
            "Watch it run mobile and desktop performance benchmarks",
            "Copy the exact code snippets Claude generates to double your page speed"
        ]
    },
    {
        "title": "The Secret Skill That Turns Claude Into a Local Voice Studio",
        "tool_name": "Voice-Studio Skill",
        "skill_category": "Creative Audio",
        "cta_keyword": "SPEECH",
        "resource_url": "https://github.com/thewh1teagle/kokoro-onnx",
        "premise": "Instead of paying monthly ElevenLabs fees, developers connected Kokoro ONNX to Claude. Claude writes the script, formats phonemes, and synthesizes broadcast-quality human speech running entirely offline on your local computer.",
        "steps": [
            "Install the lightweight Kokoro voice engine locally",
            "Ask Claude to generate narration with natural pauses",
            "Export studio-quality WAV files with zero subscription fees"
        ]
    },
    {
        "title": "Dockerize Any Complex Codebase With Zero Configuration",
        "tool_name": "Docker-Architect Skill",
        "skill_category": "DevOps",
        "cta_keyword": "DOCKER",
        "resource_url": "https://github.com/modelcontextprotocol/servers",
        "premise": "Setting up Dockerfiles and docker-compose configurations for multi-container apps usually takes hours of debugging port conflicts and missing Linux dependencies. This skill analyzes your repository structure and generates hardened production Docker containers on the first attempt.",
        "steps": [
            "Point Claude to your project root directory",
            "Say 'Dockerize this app for production deployment'",
            "Run 'docker compose up' and launch your app without touching terminal configs"
        ]
    }
]

def get_random_claude_skill():
    """Returns a high-converting Claude Skill exploit."""
    return random.choice(CLAUDE_SKILLS_CATALOG)
