# Risk Analysis Frontend Features

## Overview

This document describes the new risk analysis features added to the TopDeck frontend. These enhancements enable users to run tests on resources and ask questions about their infrastructure, improving the platform's usability and value.

## New Features

### 1. Resource Testing Suite

The Resource Testing Suite allows users to run various types of tests on their cloud resources:

**Features:**
- **Multiple Test Suites:**
  - Health Check: Validates resource availability and dependency health
  - Performance Test: Checks response times and throughput
  - Security Scan: Identifies single points of failure, blast radius, and configuration issues
  - Comprehensive Test: Runs all tests together

**How to Use:**
1. Navigate to Risk Analysis page
2. Select the "Resource Testing" tab
3. Choose a resource from the dropdown
4. Select a test suite (Health Check, Performance, Security, or Comprehensive)
5. Click "Run Tests"
6. View detailed test results with pass/fail status, duration, and recommendations

**Test Results Include:**
- Test pass/fail/warning status
- Execution duration for each test
- Affected services count
- Detailed recommendations for failed tests

### 2. Resource Query Assistant

An intelligent assistant that answers natural language questions about your infrastructure:

**Supported Queries:**
- "What resources depend on [resource-name]?"
- "Which resources are single points of failure?"
- "What is the risk score for [resource-name]?"
- "Show me all databases in Azure"
- "What would happen if [resource-name] fails?"

**Features:**
- Natural language processing of queries
- Contextual responses with relevant data
- Suggestion chips for follow-up questions
- Conversation history
- Integration with backend risk analysis APIs

**How to Use:**
1. Navigate to Risk Analysis page
2. Select the "Query Assistant" tab
3. Type your question in the text field or click an example query
4. Receive intelligent responses with resource details and suggestions
5. Follow up with additional questions based on suggestions

### 3. Enhanced Risk Analysis Overview

**Performance Optimizations:**
- Memoized components to reduce unnecessary re-renders
- Lazy loading of heavy components
- Efficient state management with Zustand

**UI Improvements:**
- Tabbed interface for better organization
- Overview, Resource Testing, Query Assistant, and Risk Breakdown tabs
- Color-coded risk levels (Critical, High, Medium, Low)
- Interactive charts and visualizations

### 4. Risk Breakdown Analysis

The existing Risk Breakdown component has been integrated into the new tabbed interface:

**Features:**
- Detailed breakdown of degradation, downtime, and misconfiguration risks
- Visual risk distribution charts
- List of affected services with impact levels
- Integration with backend risk assessment APIs

## Technical Implementation

### New Components

1. **ResourceTester.tsx** (`/frontend/src/components/risk/ResourceTester.tsx`)
   - Implements the testing suite UI
   - Simulates test execution with progress indicators
   - Displays results in a structured format

2. **ResourceQuery.tsx** (`/frontend/src/components/risk/ResourceQuery.tsx`)
   - Natural language query interface
   - Query parsing and processing logic
   - Conversation management

### Performance Optimizations

- Used `React.memo()` for expensive components
- Implemented `useMemo()` for computed values
- Added lazy loading for components
- Optimized re-render cycles

### TypeScript Improvements

- Fixed TypeScript `any` types with proper interfaces
- Enhanced type safety across components
- Updated type definitions in `types/index.ts`

## API Integration

The new features integrate with existing backend APIs:

- `/api/v1/risk/resources/{id}` - Risk assessment
- `/api/v1/risk/blast-radius/{id}` - Blast radius calculation
- `/api/v1/risk/spof` - Single points of failure
- `/api/v1/topology/resources/{id}/dependencies` - Resource dependencies

## Screenshots

### Overview Tab
![Risk Analysis Overview](https://github.com/user-attachments/assets/61c68e0f-baa4-40e0-a877-4812f128caa2)

### Resource Testing Tab
![Resource Testing](https://github.com/user-attachments/assets/70b66a4f-e6db-47ce-b1f1-1abf9bedb3e6)

### Query Assistant Tab
![Query Assistant](https://github.com/user-attachments/assets/a11137d3-208e-409e-aa1d-faa72cdf0f54)

### Risk Breakdown Tab
![Risk Breakdown](https://github.com/user-attachments/assets/c4bb8cdc-2d21-4def-95ac-65469c08cb91)

## Future Enhancements

- Add support for custom test scenarios
- Implement ML-based query understanding
- Add export functionality for test results
- Enable scheduling of automated tests
- Add more sophisticated query parsing
- Integrate with external testing tools

## Testing

The components have been tested with:
- TypeScript compilation
- ESLint validation
- Manual UI testing
- Build verification

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Dependencies

No new dependencies were added. The features use existing packages:
- React 19.1.1
- Material-UI 7.3.4
- TypeScript 5.9.3
