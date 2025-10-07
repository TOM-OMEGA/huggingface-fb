# Overview

This is a Facebook web scraper application built with Flask and Playwright. The application provides automated scraping of Facebook posts while maintaining session persistence through cookies. It includes a keep-alive mechanism specifically designed for Replit's environment to prevent the application from sleeping due to inactivity.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Application Structure

**Problem**: Need to scrape Facebook content programmatically while handling authentication and maintaining uptime on Replit.

**Solution**: Dual Flask server architecture with Playwright-based web scraping.

### Core Components

1. **Main Flask Application** (Port: Default/Configurable)
   - Handles primary scraping API endpoints
   - Manages post data storage and retrieval
   - Processes scraping requests

2. **Keep-Alive Server** (Port 8081)
   - Separate Flask instance to prevent Replit environment sleep
   - Provides health check endpoints (`/` and `/ping`)
   - Runs as daemon thread to avoid blocking main application
   - Includes port conflict handling with fallback logic

### Web Scraping Architecture

**Technology Choice**: Playwright (headless browser automation)

**Rationale**: 
- Handles JavaScript-rendered content on Facebook
- Manages complex authentication flows
- Provides reliable element interaction

**Alternatives Considered**:
- Simple HTTP requests (inadequate for JS-heavy sites)
- Selenium (Playwright offers better async support and lighter footprint)

### Session Management

**Cookie Persistence Strategy**:
- Session state stored in `fb_state.json`
- Enables re-authentication without repeated logins
- Reduces detection risk from excessive login attempts

**Pros**:
- Maintains session across restarts
- Reduces Facebook's anti-bot triggers

**Cons**:
- Cookies expire and require refresh
- Security consideration for credential storage

### Data Storage

**Simple JSON File System**:
- Posts stored in `posts.json`
- UTF-8 encoding for international character support
- Pretty-printed format (indent=2) for readability

**Design Decision**: File-based storage chosen for simplicity and Replit compatibility. No database overhead for straightforward data persistence needs.

## Threading Model

**Daemon Thread Pattern**:
- Keep-alive server runs on separate daemon thread
- Non-blocking initialization
- Automatic cleanup on main process termination

# External Dependencies

## Core Libraries

1. **Flask** - Web framework for both main and keep-alive servers
2. **Playwright** - Headless browser automation for web scraping
3. **Requests** - HTTP client library (likely for webhook/API calls)
4. **Cryptography** - Security library (likely for cookie encryption or secure storage)

## Platform Dependencies

- **Replit Environment**: Application designed specifically for Replit's hosting environment with sleep prevention mechanism
- **Facebook**: Target scraping platform (external service dependency)

## Configuration

Environment variables used:
- `KEEP_ALIVE_PORT` (default: 8081) - Configurable port for keep-alive server to avoid conflicts